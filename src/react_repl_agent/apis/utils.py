def dict_of_lists_to_list_of_dicts(dict_of_lists):
    """
    Python code to convert a dictionary of lists to a list of dictionaries

    Code written by ChatGPT.
    """
    # Get the keys of the dictionary
    keys = dict_of_lists.keys()
    # Get the values of the dictionary as a list of lists
    values = dict_of_lists.values()
    # Zip the keys and values together and map the resulting tuples to dictionaries
    list_of_dicts = [dict(zip(keys, vals)) for vals in zip(*values)]
    return list_of_dicts
