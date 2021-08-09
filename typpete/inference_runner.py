from pathlib import Path
from typpete.stmt_inferrer import *
from typpete.import_handler import ImportHandler
from z3 import Optimize

import argparse
import astor
import logging
import time
import typpete.config as config


logger = logging.Logger("typpete")


def configure_inference(args):
    class_type_params = None
    func_type_params = None
    for flag_name in vars(args):
        flag_value = getattr(args, flag_name)
        # func_type_params=make_object,1,d,2
        if flag_name == "func_type_params":
            if func_type_params is None or flag_value == "":
                func_type_params = {}
            else:
                flag_value = flag_value.split(",")
                for i in range(0, len(flag_value), 2):
                    func_name = flag_value[i]
                    count = int(flag_value[i + 1])
                    type_vars = ["{}{}".format(func_name, i) for i in range(count)]
                    func_type_params[func_name] = type_vars
        elif flag_name == "class_type_params":
            if class_type_params is None or flag_value == "":
                class_type_params = {}
            else:
                flag_value = flag_value.split(",")
                for i in range(0, len(flag_value), 2):
                    cls_name = flag_value[i]
                    count = int(flag_value[i + 1])
                    type_vars = ["{}{}".format(cls_name, i) for i in range(count)]
                    class_type_params[cls_name] = type_vars
        elif flag_name in config.config:
            config.config[flag_name] = flag_value == "True"
    return class_type_params, func_type_params


def run_inference(args, file_path: Path, base_folder: Path):
    start_time = time.time()
    class_type_params, func_type_params = configure_inference(args)

    if not base_folder:
        base_folder = Path("")

    file_name = file_path.stem
    t = ImportHandler.get_module_ast(file_name, base_folder)

    solver = z3_types.TypesSolver(
        t,
        base_folder=base_folder,
        type_params=func_type_params,
        class_type_params=class_type_params,
    )

    context = Context(t, t.body, solver)
    context.type_params = solver.config.type_params
    context.class_type_params = solver.config.class_type_params
    solver.infer_stubs(context, infer)

    for stmt in t.body:
        infer(stmt, context, solver)

    solver.push()
    end_time = time.time()
    logger.debug("Constraints collection took  {}s".format(end_time - start_time))

    start_time = time.time()
    if config.config["enable_soft_constraints"]:
        check = solver.optimize.check()
    else:
        check = solver.check(solver.assertions_vars)
    end_time = time.time()
    logger.debug("Constraints solving took  {}s".format(end_time - start_time))

    if args.outdir is None:
        write_path = Path("inference_output") / base_folder
    else:
        write_path = Path(args.outdir)

    if logging.DEBUG >= logging.root.level:
        write_path.mkdir(parents=True, exist_ok=True)
        log_prefix = file_name.replace("/", ".")
        file = open(write_path / Path(f"{log_prefix}_constraints_log.txt"), "w")
        file.write(print_solver(args, solver))
        file.close()

    if check == z3_types.unsat:
        print("Check: unsat")
        if config.config["print_unsat_core"]:
            print("Writing unsat core to {}".format(write_path))
            if config.config["enable_soft_constraints"]:
                solver.check(solver.assertions_vars)
                core = solver.unsat_core()
            else:
                core = solver.unsat_core()
            core_string = "\n".join(solver.assertions_errors[c] for c in core)
            file = open(write_path / Path(f"{log_prefix}_unsat_core.txt"), "w")
            file.write(core_string)
            file.close()
            model = None

            opt = Optimize(solver.ctx)
            for av in solver.assertions_vars:
                opt.add_soft(av)
            for a in solver.all_assertions:
                opt.add(a)
            for a in solver.z3_types.subtyping:
                opt.add(a)
            for a in solver.z3_types.subst_axioms:
                opt.add(a)
            for a in solver.forced:
                opt.add(a)
            start_time = time.time()
            opt.check()
            model = opt.model()
            end_time = time.time()
            print("Solving relaxed model took  {}s".format(end_time - start_time))
            for av in solver.assertions_vars:
                if not model[av]:
                    print("Unsat:")
                    print(solver.assertions_errors[av])
        else:
            opt = Optimize(solver.ctx)
            for av in solver.assertions_vars:
                opt.add_soft(av)
            for a in solver.all_assertions:
                opt.add(a)
            for a in solver.z3_types.subtyping:
                opt.add(a)
            for a in solver.z3_types.subst_axioms:
                opt.add(a)
            for a in solver.forced:
                opt.add(a)
            start_time = time.time()
            opt.check()
            model = opt.model()
            end_time = time.time()
            print("Solving relaxed model took  {}s".format(end_time - start_time))
            for av in solver.assertions_vars:
                if not model[av]:
                    print("Unsat:")
                    print(solver.assertions_errors[av])
    else:
        if config.config["enable_soft_constraints"]:
            model = solver.optimize.model()
        else:
            model = solver.model()

    if model is not None:
        context.generate_typed_ast(model, solver)
        ImportHandler.add_required_imports(file_name, t, context)

        if args.overwrite:
            write_path = base_folder
        else:
            write_path.mkdir(parents=True, exist_ok=True)
            file_path = Path(f"{file_name}.py")
        write_path = write_path / file_path
        logger.debug(f"Writing output to {write_path}")
        file = open(write_path, "w")
        file.write(astor.to_source(t))
        file.close()

        ImportHandler.write_to_files(model, solver)


def print_solver(args, z3solver):
    if args.sexpr:
        options = [
            ("auto_config", "false"),
            ("smt.mbqi", "false"),
            ("unsat_core", "true"),
        ]
        options = "\n".join([f"(set-option :{k} {v})" for k, v in options]) + "\n"
        assertions = "\n".join([f"(assert {a})" for a in z3solver.assertions_vars])
        return options + z3solver.sexpr() + "\n" + assertions + "\n(check-sat)"
    printer = z3_types.z3printer
    printer.set_pp_option("max_lines", 4000)
    printer.set_pp_option("max_width", 1000)
    printer.set_pp_option("max_visited", 10000000)
    printer.set_pp_option("max_depth", 1000000)
    printer.set_pp_option("max_args", 512)
    return str(z3solver)


def print_context(ctx, model, ind=""):
    for v in sorted(ctx.types_map):
        z3_t = ctx.types_map[v]
        if isinstance(z3_t, (Context, AnnotatedFunction)):
            continue
        try:
            t = model[z3_t]
            print(ind + "{}: {}".format(v, t if t is not None else z3_t))
        except z3_types.Z3Exception:
            print(ind + "{}: {}".format(v, z3_t))
        if ctx.has_context_in_children(v):
            print_context(ctx.get_context_from_children(v), model, "\t" + ind)
        if not ind:
            print("---------------------------")
    children = False
    for child in ctx.children_contexts:
        if ctx.name == "" and child.name == "":
            children = True
            print_context(child, model, "\t" + ind)
    if not ind and children:
        print("---------------------------")


def main(args=None):
    parser = argparse.ArgumentParser(description="Static type inference for Python 3")
    parser.add_argument(
        "--ignore-fully-annotated-function",
        type=int,
        default=argparse.SUPPRESS,
        help="Ignore the body of fully annotated functions and just take the provided types for args/return.",
    )
    parser.add_argument(
        "--enforce-same-type-in-branches",
        type=int,
        default=argparse.SUPPRESS,
        help="Allow different branches to use different types of same variable.",
    )
    parser.add_argument(
        "--allow-attributes-outside-init",
        type=int,
        default=argparse.SUPPRESS,
        help="Allow to define instance attribute outside __init__.",
    )
    parser.add_argument(
        "--none-subtype-of-all",
        type=int,
        default=argparse.SUPPRESS,
        help="Make None a sub-type of all types.",
    )
    parser.add_argument(
        "--enable-soft-constraints",
        type=int,
        default=argparse.SUPPRESS,
        help="Use soft contraints to infer more precise types for local variables.",
    )
    parser.add_argument(
        "--func-type-params",
        default="",
        help="Type parameters required by generic functions.",
    )
    parser.add_argument(
        "--class-type-params",
        default="",
        help="Type parameters required by generic classes.",
    )
    parser.add_argument(
        "-i",
        "--overwrite",
        action="store_true",
        help="Overwrite the source file. May lose comments and formatting",
    )
    parser.add_argument(
        "--sexpr", action="store_true", help="Use sexpr format for outpu"
    )
    parser.add_argument("--outdir", default=None, help="Output directory")
    parser.add_argument("-l", "--log-level", default="INFO", help="set log level")
    args, rest = parser.parse_known_args(args=args)

    try:
        logging.basicConfig(level=args.log_level)
        console = logging.StreamHandler()
        console.setLevel(logging.root.level)
        formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
        console.setFormatter(formatter)
        logger.addHandler(console)
    except ValueError:
        logging.error(f"Invalid log level: {args.log_level}")
        sys.exit(1)

    if len(rest):
        file_path = Path(rest[0])
        base_folder = Path(rest[1]) if len(rest) > 1 else file_path.parent
        run_inference(args, file_path, base_folder)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
