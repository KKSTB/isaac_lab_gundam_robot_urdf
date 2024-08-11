#!/usr/bin/env python

# This file prints and illustrates the joints in the renamed URDF
# so that it is easier to be used in projects like Isaac Sim or Isaac Lab
# Just run ./(script_name).py inside gundam_rx78_description/scripts/

import os


class UrdfConst:
    URDF_EXT = '.urdf'
    LINK_TAG_START  = '  <link name='
    LINK_TAG_END    = '  </link>\n'
    JOINT_TAG_START = '  <joint name='
    JOINT_TAG_FIXED = ' type="fixed">\n'
    JOINT_TAG_END   = '  </joint>\n'
    PARENT_TAG_START= '    <parent link='
    CHILD_TAG_START = '    <child link='
    MIMIC_TAG_START = '    <mimic joint='


def main() -> None:
    # Search for URDF, assuming this script is inside gundam_rx78_description/scripts/
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))):
        for filename in files:
            # Look for renamed URDF ending with '_'
            if filename.endswith('_' + UrdfConst.URDF_EXT):
                print_urdf(os.path.join(root, filename))

def print_urdf(urdf_path: str) -> None:
    print(urdf_path)
    with open(urdf_path, 'r') as fin:
        print_relationships(fin.readlines())

def print_relationships(urdf_lines: list[str]) -> None:
    link_list = list[str]()
    joint_list = list[tuple[str, int, int]]()
    ignore_list = list[int]()

    # Read sequentially
    # Assumes links are defined before being used in joints
    line_num = 0
    line_num_max = len(urdf_lines)
    while line_num < line_num_max:
        line_entry = urdf_lines[line_num]
        line_split = line_entry.split('"')

        match line_split[0]:
            case UrdfConst.LINK_TAG_START:
                link_name = line_split[1]
                link_list.append(link_name)

                if line_split[2] == '>\n':
                    # Skip up to the end of link tag
                    line_num += 1
                    while line_num < line_num_max and urdf_lines[line_num] != UrdfConst.LINK_TAG_END:
                        line_num += 1
            case UrdfConst.JOINT_TAG_START:
                joint_name = line_split[1]
                parent_index = None
                child_index = None

                # Ignore fixed joints
                is_ignore = line_entry.endswith(UrdfConst.JOINT_TAG_FIXED)

                line_num += 1
                while line_num < line_num_max:
                    line_entry = urdf_lines[line_num]
                    if line_entry == UrdfConst.JOINT_TAG_END:
                        break
                    line_split = line_entry.split('"')

                    match line_split[0]:
                        case UrdfConst.PARENT_TAG_START:
                            parent_index = link_list.index(line_split[1])
                        case UrdfConst.CHILD_TAG_START:
                            child_index = link_list.index(line_split[1])
                        case UrdfConst.MIMIC_TAG_START:
                            # Ignore mimic joints
                            is_ignore = True
                    line_num += 1

                joint_list.append((joint_name, parent_index, child_index))
                if is_ignore:
                    ignore_list.append(child_index)
        line_num += 1

    # Print the relationships recursively
    print_relationship(joint_list, ignore_list, link_list.index('base_link'), 0)

def print_relationship(joint_list: list[tuple[int, int]], ignore_list: list[int], link_index: int, level: int) -> None:
    for joint_name, parent_index, child_index in joint_list:
        if parent_index == link_index:
            is_print = not child_index in ignore_list
            if is_print:
                print('-' * level + joint_name)
            print_relationship(joint_list, ignore_list, child_index, level + is_print)

if __name__ == '__main__':
    main()