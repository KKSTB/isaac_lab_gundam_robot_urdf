#!/usr/bin/env python

# This file renames 'rx78_Null_xxx_link' in URDF to meaningful names
# and resizes the robot by 1:10
# so that it is easier to be used in projects like Isaac Sim or Isaac Lab
# Just run ./(script_name).py inside gundam_rx78_description/scripts/

import os


class UrdfConst:
    RESIZE_SCALE    = 0.1
    URDF_EXT        = '.urdf'
    JOINT_TAG       = ('<joint name="', '" type="revolute">')
    CHILD_TAG       = ('<child link="', '"/>')
    ORIGIN_TAG      = ('<origin xyz="', '" rpy="')
    MASS_TAG        = ('<mass value="', '"/>')
    INERTIA_TAG     = ('<inertia ixx="', '" ixy="', '" ixz="', '" iyy="', '" iyz="', '" izz="', '"/>')
    MESH_TAG        = ('<mesh filename="', '"/>')


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
            fout.writelines(do_resize(do_rename(fin.readlines())))

def do_rename(urdf_lines: list[str]) -> list[str]:
    joint_link_relationship = dict[str, str]()

    for line_num, urdf_line in enumerate(urdf_lines):
        # Search joint names
        line_entry = urdf_line.strip()
        if not line_entry.startswith(UrdfConst.JOINT_TAG[0]) or not line_entry.endswith(UrdfConst.JOINT_TAG[1]):
            continue
        joint_name = line_entry[len(UrdfConst.JOINT_TAG[0]):-len(UrdfConst.JOINT_TAG[1])]

        # Search child link
        for joint_line in urdf_lines[line_num + 1:]:
            line_entry = joint_line.strip()
            if not line_entry.startswith(UrdfConst.CHILD_TAG[0]) or not line_entry.endswith(UrdfConst.CHILD_TAG[1]):
                continue
            link_name = line_entry[len(UrdfConst.CHILD_TAG[0]):-len(UrdfConst.CHILD_TAG[1])]
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
        urdf_line = resize_values(urdf_line, UrdfConst.RESIZE_SCALE, UrdfConst.ORIGIN_TAG)
        urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 3), UrdfConst.MASS_TAG)
        urdf_line = resize_values(urdf_line, pow(UrdfConst.RESIZE_SCALE, 5), UrdfConst.INERTIA_TAG)
        urdf_line = resize_mesh(urdf_line, UrdfConst.RESIZE_SCALE, UrdfConst.MESH_TAG)
        urdf_lines[line_num] = urdf_line

    return urdf_lines

def resize_values(urdf_line: str, resize_scale: float, find_substrings: list[str]) -> str:
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
    index_start = urdf_line.find(find_substrings[0])
    index_end = urdf_line.find(find_substrings[1])
    if index_start < 0 or index_end < 0:
        return urdf_line

    urdf_line = urdf_line[:index_end] + '" scale="' + str(resize_scale) + ' ' + str(resize_scale) + ' ' + str(resize_scale) + urdf_line[index_end:]
    return urdf_line

if __name__ == '__main__':
    main()