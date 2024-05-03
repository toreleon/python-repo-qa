PROMPT = """Task:Generate Cypher statement to
query a graph database.
Instructions:
Use only the provided relationship types and properties in the
schema. Do not use any other relationship types or properties that
are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than
for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher
statements for particular questions:

#Explain all methods in the class inside the sort_algorithms.quick_sort module?
MATCH (:Module{{name:"sort_algorithms.quick_sort"}})-[:CONTAINS]->(:Class)-[:CONTAINS]->(m:Method)

Output:
The code snippet you've provided outlines a class that implements the Quick Sort algorithm for sorting a list. The Quick Sort algorithm is a divide-and-conquer algorithm that selects a 'pivot' element from the array and partitions the other elements into two sub-arrays, according to whether they are less than or greater than the pivot. The sub-arrays are then sorted recursively. This implementation includes a constructor, a process method to initiate the sorting, the quick_sort method itself, and a partition method used within quick_sort. Let's go through each method:

__init__(self, data): This is the constructor method for the class. It is called when an instance of the class is created. The super().__init__(data) call is attempting to call the constructor of the base class (which isn't explicitly shown in this snippet, so we'll assume this class is meant to inherit from another class that takes data as an initialization parameter). This method initializes the instance with the data to be sorted.

process(self): This method serves as a public interface to start the sorting process. It calls the quick_sort method with the initial indices of the list to be sorted (i.e., from the first element 0 to the last element len(self.data) - 1). After the sorting is done, it returns the sorted data.

quick_sort(self, low, high): This is the method that implements the Quick Sort algorithm. It takes two arguments, low and high, which are the indices of the start and end of the segment of the list to be sorted. If the segment contains more than one element (low < high), it finds the partition index pi by calling the partition method. The list is then divided into two parts: elements less than the pivot are placed before pi, and elements greater than the pivot are placed after pi. The method then recursively sorts the sub-arrays before and after the partition index.

partition(self, low, high): This method is responsible for partitioning the segment of the list between low and high indices around a pivot element. The pivot is chosen to be the element at the high index. The method then rearranges the elements in the list so that all elements less than the pivot come before the pivot, while all elements greater than the pivot come after it. The method keeps an index i to place the pivot in its correct position in the sorted array and moves all smaller (smaller than pivot) to the left of the pivot and all greater elements to the right of the pivot. Finally, it places the pivot in its correct position and returns the index of the pivot, so the quick_sort method can use it for further partitioning.

This implementation of Quick Sort is in-place, meaning it does not require additional storage proportional to the size of the input array, making it efficient in terms of space. Quick Sort has an average and best-case time complexity of O(n log n), but its worst-case time complexity is O(n^2), which occurs when the smallest or largest element is always chosen as the pivot. However, with good pivot selection methods, Quick Sort is very efficient and is often used in practice.

The question is:
{question}"""