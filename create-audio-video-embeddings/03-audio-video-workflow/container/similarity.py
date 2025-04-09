# cosine similarity between two dense vectors
import numpy as np
def cosine_similarity(a, b):
    """
    Calculates the cosine similarity between two vectors.

    Args:
        a (numpy.ndarray): The first vector.
        b (numpy.ndarray): The second vector.

    Returns:
        float: The cosine similarity between the two vectors.
    """
    # Calculate the dot product of the two vectors
    dot_product = np.dot(a, b)
    
    # Calculate the magnitude (L2 norm) of the first vector
    magnitude_a = np.linalg.norm(a)
    
    # Calculate the magnitude (L2 norm) of the second vector
    magnitude_b = np.linalg.norm(b)
    
    # Calculate the cosine similarity
    similarity = dot_product / (magnitude_a * magnitude_b)
    
    return similarity



# for a list of vectors, calculate the cosine similarity between each pair of vectors
def cosine_similarity_list(vectors):
    """
    Calculates the cosine similarity between each pair of vectors in a list.

    Args:
        vectors (list): A list of vectors.

    Returns:
        list: A list of cosine similarities between each pair of vectors.
    """
    similarities = []
    for i in range(len(vectors)-1):
        similarities.append(cosine_similarity(vectors[i], vectors[i+1]))
    return similarities





def filter_relevant_frames(frames_sim,difference_threshold = 0.8):
    selected_frames = []
    for index, sim in enumerate(frames_sim):
        print (index, end="")
        if sim < difference_threshold:
            selected_frames.append(index)
    return selected_frames