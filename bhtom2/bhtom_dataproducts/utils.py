
def map_data_from_cpcs(columns,data_to_map):
    result = []
    for data in data_to_map:
       mapping = {column: value for column, value in zip(columns, data)}
       result.append(mapping)
     
    return result
