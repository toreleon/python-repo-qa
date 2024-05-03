import ast
import os
import builtins
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts.prompt import PromptTemplate
from langchain_openai import ChatOpenAI
from code_graph import CodeGraphNeo4j
from schemas import *
from prompt import PROMPT

NEO4J_URI="neo4j+s://89bf027c.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="sbQ7D9glzKPHV8LDvdbfFMPYBINUKI7IsFmvW0SEwnE"
NEO4J_DATABASE="neo4j"

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, uri, user, password, module_name, *args, **kwargs):
        super().__init__()
        self.graph = CodeGraphNeo4j(uri, user, password)
        self.current_module_name = module_name
        self.current_function = None
        self.current_class = None
        self.known_instances = {}

    def visit_FunctionDef(self, node):
        function = Function(
            name=node.name,
            parameters=[arg.arg for arg in node.args.args],
            return_type=ast.unparse(node.returns) if node.returns else None,
            docstring=ast.get_docstring(node),
            code_snippet=ast.unparse(node),
            line_number=node.lineno
        )
        if self.current_class:
            self.graph.add_method_to_class(self.current_class, function)
        else:
            self.graph.add_function(function, self.current_module_name)
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_Import(self, node):
        for alias in node.names:
            self.graph.add_import(alias.name)
            # Assuming self.current_module_name is the name of the module being analyzed
            self.graph.add_import_relationship(self.current_module_name, alias.name)

    def visit_ImportFrom(self, node):
        module_name = node.module if node.module else ""
        for alias in node.names:
            imported_name = alias.name
            self.graph.add_import(module_name + "." + imported_name)
            # Add a relationship from the current module to the imported symbol
            self.graph.add_import_relationship(self.current_module_name, module_name + "." + imported_name)

    def visit_ClassDef(self, node):
        class_ = Class(
            name=node.name,
            methods=[],  # This will be populated by visit_FunctionDef
            attributes=[],  # This will be populated by visit_Assign if needed
            base_classes=[ast.unparse(base) for base in node.bases],
            docstring=ast.get_docstring(node),
            is_abstract=any(isinstance(d, ast.FunctionDef) and d.name.startswith('__') for d in node.body)
        )
        self.graph.add_class(class_, self.current_module_name)

        # Handle inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.graph.add_inheritance(node.name, base.id)
            elif isinstance(base, ast.Attribute):  # Handle cases like module.Class
                base_name = ast.unparse(base)
                self.graph.add_inheritance(node.name, base_name)

        self.current_class = node.name  # Track the current class for nested functions or variables
        self.generic_visit(node)
        self.current_class = None  # Reset after leaving the class

    def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variable_name = target.id
                    self.handle_rhs(node.value, variable_name)
            self.generic_visit(node)

    def handle_rhs(self, rhs, variable_name):
        if isinstance(rhs, ast.Name):
            # RHS is a variable
            self.graph.add_variable_usage(variable_name, rhs.id)
        elif isinstance(rhs, ast.Call):
            # RHS is a function call
            if isinstance(rhs.func, ast.Name):
                callee = rhs.func.id
                self.graph.add_call(variable_name, callee)
            elif isinstance(rhs.func, ast.Attribute):
                # Handle method calls
                callee = f"{ast.unparse(rhs.func.value)}.{rhs.func.attr}"
                self.graph.add_call(variable_name, callee)
        elif isinstance(rhs, ast.Attribute):
            # RHS is an attribute access, potentially a class instantiation
            self.graph.add_creates(variable_name, ast.unparse(rhs))

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            callee_method = node.func.attr
            callee_object_class = None
            if isinstance(node.func.value, ast.Name):
                callee_object = node.func.value.id
                if callee_object in self.known_instances:
                    callee_object_class = self.known_instances[callee_object]
                if callee_object_class:
                    self.graph.add_call(self.current_function, f"{callee_object_class}.{callee_method}")
        elif isinstance(node.func, ast.Name):
            callee_function = node.func.id
            if not hasattr(builtins, callee_function):
                self.graph.add_call(self.current_function, callee_function)
        self.generic_visit(node)

    def add_variable_usage_edges(self, value_node, variable_name):
        # This function adds edges from variables used in value_node to the defined variable_name
        if isinstance(value_node, ast.Name):
            self.graph.add_variable_usage(value_node.id, variable_name)
        elif isinstance(value_node, ast.BinOp):
            self.add_variable_usage_edges(value_node.left, variable_name)
            self.add_variable_usage_edges(value_node.right, variable_name)

    def visit_Name(self, node):
        # This method is called for every instance of ast.Name, which is used for variable references
        if isinstance(node.ctx, ast.Load):  # This checks if the variable is being read
            if self.current_function:
                self.graph.add_variable_usage(self.current_function, node.id)
        self.generic_visit(node)


def parse_repository(directory_path, uri, user, password):
    # Initialize the CodeGraphNeo4j connection
    graph = CodeGraphNeo4j(uri, user, password)
    # Clear the database once before processing the files
    graph.clear_database()
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith('.py'):  # Check if the file is a Python file
                file_path = os.path.join(root, file_name)
                # Create a new CodeAnalyzer instance for each Python file
                module_name = compute_module_name(directory_path, file_path)
                analyzer = CodeAnalyzer(uri, user, password, module_name)
                with open(file_path, "r") as source:
                    try:
                        tree = ast.parse(source.read(), filename=file_path)
                        analyzer.visit(tree)
                        analyzer.graph.close()
                    except SyntaxError as e:
                        print(f"Syntax error in {file_path}: {e}")

def compute_module_name(root_path, file_path):
    # Remove the root path and extension, and replace os-specific path separators with '.'
    relative_path = os.path.relpath(file_path, root_path)
    if relative_path.endswith('__init__.py'):
        # For __init__.py, the module name is the package name
        module_name = os.path.dirname(relative_path)
    else:
        module_name = os.path.splitext(relative_path)[0]
    return module_name.replace(os.sep, '.')


# graph = parse_repository("scikit-learn", NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
KNOWLEDGE_GRAPH = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
    enhanced_schema=True,
)

# print(KNOWLEDGE_GRAPH.schema)

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=PROMPT
)

cypherChain = GraphCypherQAChain.from_llm(
    ChatOpenAI(
        model="gpt-3.5-turbo-0125",
        temperature=0, 
        openai_api_key=OPENAI_API_KEY
        ),
    graph=KNOWLEDGE_GRAPH,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
)

import streamlit as st

# Assuming cypherChain.invoke is defined elsewhere and imported correctly
# from yourmodule import cypherChain

def main():
    st.title("CypherChain Query Interface")

    # Text input box for the user to enter a query
    query = st.text_input("Enter a question:", "")

    # Button to invoke the cypherChain with the query
    if st.button("Submit"):
        try:
            # Assuming cypherChain.invoke returns a dictionary with a "result" key
            response = cypherChain.invoke(query)
            if "result" in response:
                st.success(response["result"])
            else:
                st.error("No result found in the response.")
        except Exception as e:
            # Display the error to the user
            st.success("I don't have an answer for that question.")

if __name__ == "__main__":
    main()