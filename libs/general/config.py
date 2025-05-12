from LauncherBase import Base


def write_global_config(item_name, new_item_data):
    found = False
    with open(Base.global_config_path, 'r') as file:
        lines = file.readlines()
        for i in range(len(lines)):
            if item_name in lines[i]:
                # Use the new or existing account ID
                lines[i] = f'{item_name} = "{new_item_data}"\n'
                found = True
    with open(Base.global_config_path, 'w') as file:
        file.writelines(lines)
    if found:
        return True
    else:
        return False
