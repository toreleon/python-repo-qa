import logging
import networkx as nx
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_function(self, function):
        self.graph.add_node(function.name, type='function', details=function)
        logger.info(f"Added function: {function.name}")

    def add_class(self, class_):
        self.graph.add_node(class_.name, type='class', details=class_)
        logger.info(f"Added class: {class_.name}")

    def add_module(self, module):
        self.graph.add_node(module.name, type='module', details=module)
        logger.info(f"Added module: {module.name}")

    def add_variable(self, variable):
        self.graph.add_node(variable.name, type='variable', details=variable)
        logger.info(f"Added variable: {variable.name}")

    def add_import(self, import_name):
        self.graph.add_node(import_name, type='import')
        logger.info(f"Added import: {import_name}")

    def add_call(self, caller, callee):
        self.graph.add_edge(str(caller), callee, type='calls')
        logger.info(f"Added call: {caller} -> {callee}")

    def add_inheritance(self, subclass, superclass):
        self.graph.add_edge(subclass, superclass, type='inherits')
        logger.info(f"Added inheritance: {subclass} -> {superclass}")

    def add_variable_usage(self, user, used):
        self.graph.add_edge(user, used, type='uses')
        logger.info(f"Added variable usage: {user} -> {used}")

    def add_creates(self, creator, created):
        self.graph.add_edge(creator, created, type='creates')
        logger.info(f"Added creation: {creator} -> {created}")

    def add_method_to_class(self, class_name, method):
        # Ensure the class exists in the graph
        if class_name in self.graph:
            # Add method as a node
            method_full_name = f"{class_name}.{method.name}"
            self.graph.add_node(method_full_name, type='method', details=method)
            # Link method to its class
            self.graph.add_edge(class_name, method_full_name, type='contains')
        else:
            print(f"Error: Class '{class_name}' not found in graph.")

class CodeGraphNeo4j:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        try:
            with self.driver.session() as session:
                result = session.write_transaction(self._create_and_return, query, parameters)
                return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")

    @staticmethod
    def _create_and_return(tx, query, parameters):
        result = tx.run(query, parameters)
        return [record for record in result]

    def add_function(self, function, module_name):
        query = (
            "MERGE (f:Function {name: $name}) "
            "ON CREATE SET f.details = $details "
            "WITH f "
            "MERGE (m:Module {name: $module_name}) "
            "MERGE (m)-[:CONTAINS]->(f)"
        )
        self.execute_query(query, {'name': function.name, 'details': str(function), 'module_name': module_name})
        logger.info(f"Added function: {function.name} to module: {module_name}")

    def add_class(self, class_, module_name):
        query = (
            "MERGE (c:Class {name: $name}) "
            "ON CREATE SET c.details = $details "
            "WITH c "
            "MERGE (m:Module {name: $module_name}) "
            "MERGE (m)-[:CONTAINS]->(c)"
        )
        self.execute_query(query, {'name': class_.name, 'details': str(class_), 'module_name': module_name})
        logger.info(f"Added class: {class_.name} to module: {module_name}")

    def add_variable(self, variable, module_name):
        query = (
            "MERGE (v:Variable {name: $name, details: $details}) "
            "WITH v "
            "MERGE (m:Module {name: $module_name}) "
            "MERGE (m)-[:CONTAINS]->(v)"
        )
        self.execute_query(query, {'name': variable.name, 'details': str(variable), 'module_name': module_name})
        logger.info(f"Added variable: {variable.name} to module: {module_name}")


    def add_module(self, module):
        query = (
            "CREATE (a:Module {name: $name, details: $details})"
        )
        self.execute_query(query, {'name': module.name, 'details': str(module)})
        logger.info(f"Added module: {module.name}")

    def add_import(self, import_name):
        query = (
            "MERGE (a:Import {name: $name})"
        )
        self.execute_query(query, {'name': import_name})
        logger.info(f"Added import: {import_name}")


    def add_call(self, caller, callee):
        query = (
            "MERGE (caller {name: $caller}) "  # Specify the correct label if known, e.g., :Function or :Method
            "MERGE (callee {name: $callee}) "  # Specify the correct label if known
            "MERGE (caller)-[:CALLS]->(callee)"
        )
        self.execute_query(query, {'caller': caller, 'callee': callee})
        logger.info(f"Added call: {caller} -> {callee}")


    def add_inheritance(self, subclass, superclass):
        query = (
            "MERGE (subclass:Class {name: $subclass}) "
            "MERGE (superclass:Class {name: $superclass}) "
            "MERGE (subclass)-[:INHERITS_FROM]->(superclass)"
        )
        self.execute_query(query, {'subclass': subclass, 'superclass': superclass})
        logger.info(f"Added inheritance: {subclass} -> {superclass}")


    def add_variable_usage(self, user, used):
        query = (
            "MERGE (user {name: $user}) "  # Adjust with the correct label, e.g., :Function, :Method, or :Variable
            "MERGE (used:Variable {name: $used}) "
            "MERGE (user)-[:USES]->(used)"
        )
        self.execute_query(query, {'user': user, 'used': used})
        logger.info(f"Added variable usage: {user} -> {used}")


    def add_creates(self, creator, created):
        query = (
            "MERGE (creator {name: $creator}) "  # Adjust with the correct label
            "MERGE (created {name: $created}) "  # Adjust with the correct label
            "MERGE (creator)-[:CREATES]->(created)"
        )
        self.execute_query(query, {'creator': creator, 'created': created})
        logger.info(f"Added creation: {creator} -> {created}")


    def add_method_to_class(self, class_name, method):
        query = (
            "MERGE (class:Class {name: $class_name}) "
            "MERGE (method:Method {name: $method_name, details: $details}) "
            "MERGE (class)-[:CONTAINS]->(method)"
        )
        parameters = {
            'class_name': class_name,
            'method_name': method.name,
            'details': str(method)
        }
        self.execute_query(query, parameters)
        logger.info(f"Added method: {method.name} to class: {class_name}")

    def add_import_relationship(self, importer, imported):
        query = (
            "MERGE (importer:Module {name: $importer}) "
            "MERGE (imported {name: $imported}) "  # Adjust the label based on what's being imported
            "MERGE (importer)-[:IMPORTS]->(imported)"
        )
        self.execute_query(query, {'importer': importer, 'imported': imported})
        logger.info(f"Added import relationship: {importer} -> {imported}")


    def clear_database(self):
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        logger.info("Cleared database")
