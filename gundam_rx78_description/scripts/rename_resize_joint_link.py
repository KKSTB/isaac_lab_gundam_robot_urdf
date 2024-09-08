#!/usr/bin/env python

# This file renames 'rx78_Null_xxx_link' in URDF to meaningful names
# and resizes the robot by 1:10
# so that it is easier to be used in projects like Isaac Sim or Isaac Lab
# Just run ./(script_name).py inside gundam_rx78_description/scripts/

import os


class UrdfConst:
    RESIZE_SCALE    = 0.1
    USE_URDF_IMPORTER_SCALING = True    # Use "Stage Units Per Meter" to scale down the model, to avoid collision mesh bug
    MIMIC_MARGIN    = 1.25              # Add some margins to mimic joint limits to hopefully solve crash bug during RL training
    FIX_MIMIC_JOINTS= False             # Set mimic joints to fixed to hopefully solve crash bug during RL training

    URDF_EXT        = '.urdf'
    JOINT_TAG       = ('<joint name="', '" type="revolute">')
    CHILD_TAG       = ('<child link="', '"/>')
    ORIGIN_TAG      = ('<origin xyz="', '" rpy="')
    MASS_TAG        = ('<mass value="', '"/>')
    INERTIA_TAG     = ('<inertia ixx="', '" ixy="', '" ixz="', '" iyy="', '" iyz="', '" izz="', '"/>')
    EFFORT_TAG      = ('<limit effort="', '" lower="')
    DYNAMICS_TAG    = ('<dynamics damping="', '" friction="', '"/>')
    MESH_TAG        = ('<mesh filename="', '"/>')
    MIMIC_TAG       = ('<mimic joint="', '" multiplier="', '" offset="', '"/>')
    LIMIT_TAG       = ('<limit effort="', '" lower="', '" upper="', '" velocity="', '"/>')
    JOINT_END_TAG   = ('</joint>',)


def main() -> None:
    # Search for URDF, assuming this script is inside gundam_rx78_description/scripts/
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))):
        for filename in files:
            # Ignore URDF ending with '_' to prevent editing the previous file again
            if filename.endswith(UrdfConst.URDF_EXT) and not filename.endswith('_' + UrdfConst.URDF_EXT):
                modify_urdf(os.path.join(root, filename))

def modify_urdf(urdf_path: str) -> None:
    # Read the original URDF and write to another file with '_' appended to the name
    write_path = urdf_path[:-len(UrdfConst.URDF_EXT)] + '_' + UrdfConst.URDF_EXT
    with open(urdf_path, 'r') as fin:
        with open(write_path, 'w+') as fout:
            fout.writelines(fix_mimic_joints(adjust_mimic_limit(do_resize(do_rename(fin.readlines())))))

def do_rename(urdf_lines: list[str]) -> list[str]:
    joint_link_relationship = dict[str, str]()

    for line_num, urdf_line in enumerate(urdf_lines):
        # Search joint names
        line_entry = urdf_line.strip()
        if not line_entry.startswith(UrdfConst.JOINT_TAG[0]) or not line_entry.endswith(UrdfConst.JOINT_TAG[-1]):
            continue
        joint_name = line_entry[len(UrdfConst.JOINT_TAG[0]):-len(UrdfConst.JOINT_TAG[-1])]

        # Search child link
        for joint_line in urdf_lines[line_num + 1:]:
            line_entry = joint_line.strip()
            if not line_entry.startswith(UrdfConst.CHILD_TAG[0]) or not line_entry.endswith(UrdfConst.CHILD_TAG[-1]):
                continue
            link_name = line_entry[len(UrdfConst.CHILD_TAG[0]):-len(UrdfConst.CHILD_TAG[-1])]
            # Build the relationship dict
            joint_link_relationship[joint_name] = link_name
            break

    # Do the rename process
    for line_num, urdf_line in enumerate(urdf_lines):
        for joint_name, link_name in joint_link_relationship.items():
            # Replace joint name so that it can be easier for searching
            urdf_line = urdf_line.replace('"' + joint_name + '"', '"' + joint_name + '_joint"')
            # Replace link name with meaningful name
            urdf_line = urdf_line.replace('"' + link_name + '"', '"' + joint_name + '_link"')
        urdf_lines[line_num] = urdf_line

    return urdf_lines

def do_resize(urdf_lines: list[str]) -> list[str]:
    for line_num, urdf_line in enumerate(urdf_lines):
        # m
        if not UrdfConst.USE_URDF_IMPORTER_SCALING:
            urdf_line = resize_values(urdf_line, UrdfConst.RESIZE_SCALE, UrdfConst.ORIGIN_TAG)
        # kg
        urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 3), UrdfConst.MASS_TAG)
        # kg m^2
        if not UrdfConst.USE_URDF_IMPORTER_SCALING:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 5), UrdfConst.INERTIA_TAG)
        else:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 3), UrdfConst.INERTIA_TAG)
        # kg m^2 s^-2
        # Further scale down by 10
        if not UrdfConst.USE_URDF_IMPORTER_SCALING:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 6), UrdfConst.EFFORT_TAG)
        else:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 4), UrdfConst.EFFORT_TAG)
        # kg m s^-2
        if not UrdfConst.USE_URDF_IMPORTER_SCALING:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 4), UrdfConst.DYNAMICS_TAG)
        else:
            urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 3), UrdfConst.DYNAMICS_TAG)
        # m
        if not UrdfConst.USE_URDF_IMPORTER_SCALING:
            urdf_line = resize_mesh(urdf_line, UrdfConst.RESIZE_SCALE, UrdfConst.MESH_TAG)

        urdf_lines[line_num] = urdf_line

    return urdf_lines

def resize_values(urdf_line: str, resize_scale: float, find_substrings: list[str]) -> str:
    # Resize all values in between substrings
    for index in range(len(find_substrings) - 1):
        urdf_line = resize_value(urdf_line, resize_scale, find_substrings[index:])
    return urdf_line

def resize_value(urdf_line: str, resize_scale: float, find_substrings: list[str]) -> str:
    index_start = urdf_line.find(find_substrings[0])
    index_end = urdf_line.find(find_substrings[1])
    if index_start < 0 or index_end < 0:
        return urdf_line

    values = urdf_line[index_start + len(find_substrings[0]):index_end]
    values = [float(val) * resize_scale for val in values.split(' ')]
    values = ' '.join([str(val) for val in values])
    urdf_line = urdf_line[:index_start + len(find_substrings[0])] + values + urdf_line[index_end:]
    return urdf_line

def resize_mesh(urdf_line: str, resize_scale: float, find_substrings: list[str]) -> str:
    # Add "scale=" after all mesh tags
    index_start = urdf_line.find(find_substrings[0])
    index_end = urdf_line.find(find_substrings[1])
    if index_start < 0 or index_end < 0:
        return urdf_line

    urdf_line = urdf_line[:index_end] + '" scale="' + str(resize_scale) + ' ' + str(resize_scale) + ' ' + str(resize_scale) + urdf_line[index_end:]
    return urdf_line

def adjust_mimic_limit(urdf_lines: list[str]) -> list[str]:
    joint_limits = dict[str, tuple[float, float]]()

    # Get joint limits
    for line_num, urdf_line in enumerate(urdf_lines):
        # Look for joints
        line_entry = urdf_line.strip()
        if not line_entry.startswith(UrdfConst.JOINT_TAG[0]) or not line_entry.endswith(UrdfConst.JOINT_TAG[-1]):
            continue
        joint_name = line_entry[len(UrdfConst.JOINT_TAG[0]):-len(UrdfConst.JOINT_TAG[-1])]

        # Look for limit tag
        for joint_line in urdf_lines[line_num + 1:]:
            line_entry = joint_line.strip()
            if not line_entry.startswith(UrdfConst.LIMIT_TAG[0]) or not line_entry.endswith(UrdfConst.LIMIT_TAG[-1]):
                continue
            lower_start_pos = line_entry.find(UrdfConst.LIMIT_TAG[1]) + len(UrdfConst.LIMIT_TAG[1])
            lower_end_pos = line_entry.find(UrdfConst.LIMIT_TAG[2])
            upper_start_pos = lower_end_pos + len(UrdfConst.LIMIT_TAG[2])
            upper_end_pos = line_entry.find(UrdfConst.LIMIT_TAG[3])
            lower_value = float(line_entry[lower_start_pos:lower_end_pos])
            upper_value = float(line_entry[upper_start_pos:upper_end_pos])
            joint_limits[joint_name] = (lower_value, upper_value)
            break

    # Calculate and modify mimic joint limits
    for line_num, urdf_line in enumerate(urdf_lines):
        # Look for joints
        line_entry = urdf_line.strip()
        if not line_entry.startswith(UrdfConst.JOINT_TAG[0]) or not line_entry.endswith(UrdfConst.JOINT_TAG[-1]):
            continue

        # Look for mimic tag
        limit_line_num = None
        for joint_num, joint_line in enumerate(urdf_lines[line_num + 1:]):
            line_entry = joint_line.strip()
            if line_entry == UrdfConst.JOINT_END_TAG[0]:
                break
            if line_entry.startswith(UrdfConst.LIMIT_TAG[0]) and line_entry.endswith(UrdfConst.LIMIT_TAG[-1]):
                limit_line_num = joint_num + line_num + 1
            elif line_entry.startswith(UrdfConst.MIMIC_TAG[0]) and line_entry.endswith(UrdfConst.MIMIC_TAG[-1]):
                if limit_line_num is None:
                    break

                # Parse reference joint, multiplier and offset
                joint_start_pos = len(UrdfConst.MIMIC_TAG[0])
                joint_end_pos = line_entry.find(UrdfConst.MIMIC_TAG[1])
                multiplier_start_pos = joint_end_pos + len(UrdfConst.MIMIC_TAG[1])
                multiplier_end_pos = line_entry.find(UrdfConst.MIMIC_TAG[2])
                if multiplier_end_pos >= 0:
                    offset_start_pos = multiplier_end_pos + len(UrdfConst.MIMIC_TAG[2])
                    offset_end_pos = line_entry.find(UrdfConst.MIMIC_TAG[3])
                    offset_value = float(line_entry[offset_start_pos:offset_end_pos])
                else:
                    # No offset
                    offset_value = 0.0
                    multiplier_end_pos = line_entry.find(UrdfConst.MIMIC_TAG[3])
                reference_joint_limits = joint_limits[line_entry[joint_start_pos:joint_end_pos]]
                multiplier_value = float(line_entry[multiplier_start_pos:multiplier_end_pos])

                # Calculate mimic joint limits
                lower_value = (reference_joint_limits[0] * multiplier_value + offset_value) * UrdfConst.MIMIC_MARGIN
                upper_value = (reference_joint_limits[1] * multiplier_value + offset_value) * UrdfConst.MIMIC_MARGIN
                if lower_value > upper_value:
                    temp = lower_value
                    lower_value = upper_value
                    upper_value = temp

                # Update mimic joint limits
                limit_line = urdf_lines[limit_line_num]
                lower_start_pos = limit_line.find(UrdfConst.LIMIT_TAG[1]) + len(UrdfConst.LIMIT_TAG[1])
                lower_end_pos = limit_line.find(UrdfConst.LIMIT_TAG[2])
                upper_start_pos = lower_end_pos + len(UrdfConst.LIMIT_TAG[2])
                upper_end_pos = limit_line.find(UrdfConst.LIMIT_TAG[3])
                urdf_lines[limit_line_num] = limit_line[:lower_start_pos] + str(lower_value) + limit_line[lower_end_pos:upper_start_pos] + str(upper_value) + limit_line[upper_end_pos:]
                break

    return urdf_lines

def fix_mimic_joints(urdf_lines: list[str]) -> list[str]:
    if not UrdfConst.FIX_MIMIC_JOINTS:
        return urdf_lines

    for line_num, urdf_line in enumerate(urdf_lines):
        # Look for joints
        line_entry = urdf_line.strip()
        if not line_entry.startswith(UrdfConst.JOINT_TAG[0]) or not line_entry.endswith(UrdfConst.JOINT_TAG[-1]):
            continue

        # Look for mimic tag
        for joint_line in urdf_lines[line_num + 1:]:
            line_entry = joint_line.strip()
            if line_entry == UrdfConst.JOINT_END_TAG[0]:
                break
            if line_entry.startswith(UrdfConst.MIMIC_TAG[0]) and line_entry.endswith(UrdfConst.MIMIC_TAG[-1]):
                joint_end_pos = urdf_line.find(UrdfConst.JOINT_TAG[-1])
                urdf_lines[line_num] = urdf_line[:joint_end_pos] + '" type="fixed">\n'
                break

    return urdf_lines

if __name__ == '__main__':
    main()