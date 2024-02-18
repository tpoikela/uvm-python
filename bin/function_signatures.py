
import argparse
import ast
import os

import openai

openai.api_key = os.environ["OPENAI_API_KEY"]
if not openai.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")



def generate_docstring(function_name: str, func_body: str):
    prompt = f"""Generate a docstring for the Python function '{function_name}'. If docstring
        exists, fix errors in it. If docstring does not exist, generate it. Add type
        annotations to the function signature if they do not exist.
        Also, comment about bugs in the function if any.

        Function definition:
        ```python
        {func_body}
        ```
        """
    # print(prompt)
    if True:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    else:
        return prompt


def extract_function_signatures(code, extract_bodies=False):
    signatures = []
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            signature = f"{node.name}("
            signature += ", ".join(arg.arg for arg in node.args.args)
            if node.args.vararg:
                signature += f", *{node.args.vararg.arg}"
            if node.args.kwarg:
                signature += f", **{node.args.kwarg.arg}"
            signature += ")"
            signatures.append(signature)
            if extract_bodies:
                # print('body is ' + str(node.body))
                body = ast.get_source_segment(code, node) or ''
                #body = ast.get_source_segment(code, node.body)
                signatures.append(body)
    return signatures


def main():
    parser = argparse.ArgumentParser(
        description="Extract function signatures from Python files."
    )
    parser.add_argument(
        "-o",
        dest="output",
        metavar="output_file",
        type=str,
        help="Output file for function signatures",
    )
    parser.add_argument(
        "--bodies",
        dest="extract_bodies",
        action="store_true",
        help="Extract full function bodies in addition to signatures",
        default=False,
    )
    parser.add_argument('-n', help='number of functions to generate', type=int)
    parser.add_argument(
        "files",
        metavar="file",
        type=str,
        nargs="+",
        help="Python files to extract function signatures from",
    )
    parser.add_argument(
        "--use_openai",
        dest="use_openai",
        action="store_true",
        help="Use OpenAI to generate docstrings",
        default=False,
    )
    args = parser.parse_args()

    signatures = []
    for filename in args.files:
        with open(filename, "r") as f:
            code = f.read()
            signatures.extend(extract_function_signatures(code, args.extract_bodies))

    n = len(signatures)
    if args.n:
        n = args.n
        if args.extract_bodies:
            n = n * 2

    # Remove all but 1st n entries from signatures
    signatures = signatures[:int(n)]
    result = []
    if args.use_openai:
        for i in range(0, len(signatures), 2):
            result.append(generate_docstring(signatures[i], signatures[i + 1]))
    elif args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(signatures))
    else:
        print("\n".join(signatures))

    # Write result to file
    if args.output:
        with open(args.output, "w") as f:
            f.write("\n".join(result))
    else:
        print("\n".join(result))


if __name__ == "__main__":
    main()
