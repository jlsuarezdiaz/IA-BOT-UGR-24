import json
from itertools import product

def product_dict(**kwargs):
    keys = kwargs.keys()
    for instance in product(*kwargs.values()):
        yield dict(zip(keys, instance))

def expand_test_json(json_file):
    # Open the json file
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Create a new dictionary to store the expanded data
    expanded_data = {}

    # Iterate the data
    for key, kdict in data.items():
        if '*' not in key and '.' not in key:
            # If the key does not contain a * or ., add it to the expanded data as is
            expanded_data[key] = kdict
        # If the key contains a *, expand the data.
        else:
            if '*' in key:
                # Get the 'levels' key in the kdict
                levels = kdict['levels']
                for level in levels:

                    if '_' in key:
                        positions = kdict['positions'][str(level)]
                        for j, elem in enumerate(product_dict(**positions)):
                            # Get the j-th lowercased letter (don't use magic numbers)
                            letter = chr(97 + j)
                            new_key = key.replace('*', str(level)).replace('_', letter)
                            new_level = level
                            new_size = kdict['map_size']
                            new_type = kdict['type']
                            # For the new command, replace the * with the level
                            new_command = kdict['command'].replace('*', str(level))
                            # If key is in elem, then replace {key} in the command with the value of elem[key] (if list, join with space)
                            for k, v in elem.items():
                                print(k, v, kdict['command'])
                                new_command = new_command.replace(f'{{{k}}}', ' '.join(str(iv) for iv in v) if isinstance(v, list) else str(v))
                            # Add the new key to the expanded data
                            expanded_data[new_key] = {
                                'type': new_type,
                                'level': new_level,
                                'command': new_command,
                                'map_size': new_size
                            }

                    else:
                        # Create a new key by replacing the * with the level
                        new_key = key.replace('*', str(level))
                        new_level = level
                        new_size = kdict['map_size']
                        new_type = kdict['type']
                        # For the new command, replace the * with the level
                        new_command = kdict['command'].replace('*', str(level))
                        # Add the new key to the expanded data
                        expanded_data[new_key] = {
                            'type': new_type,
                            'level': new_level,
                            'command': new_command,
                            'map_size': new_size
                        }


    return expanded_data

if __name__ == '__main__':
    new_json = expand_test_json('tests_template.json')
    print(new_json)
    with open('tests.json', 'w') as file:
        json.dump(new_json, file, indent=4)