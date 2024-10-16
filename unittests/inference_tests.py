import builtins
import glob
import os
import unittest
from z3.z3types import Z3Exception
from z3 import simplify

import time
from typpete.stmt_inferrer import *


class TestInference(unittest.TestCase):
    def __init__(self, file_path, file_name):
        super().__init__()
        self.file_path = file_path
        self.file_name = file_name
        self.sat = True
        self.throws = None
        self.ignore = False
        self.class_type_params = None
        self.type_params = None

    @staticmethod
    def parse_comment(comment):
        assignment_text = comment[2:]  # remove the '# ' text
        variable, type_annotation = assignment_text.split(" := ")
        return variable, type_annotation

    def parse_results(self, source):
        result = {}
        for line in source:
            line = line.strip()
            if not line.startswith("#"):
                continue
            if line[2:] == "unsat":
                self.sat = False
                continue
            if line[2:] == "ignore":
                self.ignore = True
                continue
            if line[2:8] == "throws":
                self.throws = line[9:]
                continue
            if line[2:].startswith("class_type_params"):
                self.class_type_params = line[20:]
                continue
            if line[2:].startswith("type_params"):
                self.type_params = line[14:]
                continue
            variable, t = self.parse_comment(line)
            result[variable] = t
        return result

    @staticmethod
    def infer_file(path, type_params=None, class_type_params=None):
        """Infer a single python program

        :param path: file system path of the program to infer
        :return: the z3 solver used to infer the program, and the global context of the program
        """
        r = open(path)
        t = ast.parse(r.read())
        r.close()

        solver = z3_types.TypesSolver(
            t, type_params=type_params, class_type_params=class_type_params
        )

        context = Context(t, t.body, solver)

        solver.infer_stubs(context, infer)

        for stmt in t.body:
            infer(stmt, context, solver)

        solver.push()

        return solver, context

    def runTest(self):
        """Test for expressions inference"""
        start_time = time.time()
        r = open(self.file_path)
        expected_result = self.parse_results(r)
        r.close()

        if self.ignore:
            return

        if self.throws:
            self.assertRaises(
                getattr(builtins, self.throws), self.infer_file, self.file_path
            )
            end_time = time.time()
            print(self.test_end_message(end_time - start_time))
            return

        try:
            class_type_params = None
            if self.class_type_params:
                class_type_params = ast.literal_eval(self.class_type_params)
            type_params = None
            if self.type_params:
                type_params = ast.literal_eval(self.type_params)
            solver, context = self.infer_file(
                self.file_path, type_params, class_type_params
            )
        except:
            raise Exception(self.file_path)

        check = solver.optimize.check()
        if self.sat:
            self.assertNotEqual(
                check,
                z3_types.unsat,
                "Expected file {} to be SAT. Found UNSAT".format(self.file_name),
            )
        else:
            self.assertEqual(
                check,
                z3_types.unsat,
                "Expected file {} to be UNSAT. Found SAT".format(self.file_name),
            )
            end_time = time.time()
            print(self.test_end_message(end_time - start_time))
            return

        model = solver.optimize.model()
        for v in expected_result:
            self.assertTrue(
                context.has_var_in_children(v),
                "Test file {}. Expected to have variable '{}' in the program".format(
                    self.file_name, v
                ),
            )

            z3_type = context.get_var_from_children(v)
            expected = solver.annotation_resolver.resolve(
                ast.parse(expected_result[v]).body[0].value, solver, None
            )

            try:
                actual = model[z3_type]
            except Z3Exception:
                actual = z3_type
            if str(actual).startswith("generic"):
                actual = simplify(
                    getattr(solver.z3_types.type_sort, str(actual)[:8] + "_func")(
                        actual
                    )
                )
            self.assertEqual(
                actual,
                expected,
                "Test file {}. Expected variable '{}' to have type '{}', but found '{}'".format(
                    self.file_name, v, expected, actual
                ),
            )
        end_time = time.time()
        print(self.test_end_message(end_time - start_time))

    def test_end_message(self, duration):
        return "Tested {} in {:.2f} seconds.".format(self.file_name, duration)


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + "/unittests/inference/**.py"
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            name = path.split("/")[-1]
            s.addTest(TestInference(path, name))
    runner = unittest.TextTestRunner(verbosity=0)
    runner.run(s)


if __name__ == "__main__":
    suite()
