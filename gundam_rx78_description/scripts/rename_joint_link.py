#!/usr/bin/env python

import os


URDF_EXT = '.urdf'

def main() -> None:
    # Search for URDF, assuming this script is inside gundam_rx78_description/scripts/
    for root, dirs, files in os.walk(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))):
        for filename in files:
            # Ignore URDF ending with '_' to prevent editing the previous file again
            if filename.endswith(URDF_EXT) and not filename.endswith('_' + URDF_EXT):
                modify_urdf(os.path.join(root, filename))

def modify_urdf(urdf_path: str) -> None:
    # Read the original URDF and write to another file with '_' appended to the name
    write_path = urdf_path[:-len(URDF_EXT)] + '_' + URDF_EXT
    with open(urdf_path, 'r') as fin:
        with open(write_path, 'w+') as fout:
            fout.writelines(do_rename(fin.readlines()))

def do_rename(urdf_lines: list[str]) -> list[str]:
    JOINT_TAG_START = '<joint name="'
    JOINT_TAG_END   = '" type="revolute">'
    CHILD_TAG_START = '<child link="'
    CHILD_TAG_END   = '"/>'
    joint_link_relationship = dict[str, str]()

    for line_num, urdf_line in enumerate(urdf_lines):
        # Search joint names
        line_entry = urdf_line.strip()
        if not line_entry.startswith(JOINT_TAG_START) or not line_entry.endswith(JOINT_TAG_END):
            continue
        joint_name = line_entry[len(JOINT_TAG_START):-len(JOINT_TAG_END)]

        # Search child link
        for joint_line in urdf_lines[line_num + 1:]:
            line_entry = joint_line.strip()
            if not line_entry.startswith(CHILD_TAG_START) or not line_entry.endswith(CHILD_TAG_END):
                continue
            link_name = line_entry[len(CHILD_TAG_START):-len(CHILD_TAG_END)]
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

if __name__ == '__main__':
    main()