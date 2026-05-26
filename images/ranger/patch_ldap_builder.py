# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python patch_ldap_builder.py <path_to_LdapUserGroupBuilder.java>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'r') as f:
        content = f.read()

    # Define targets and replacements using tabs (\t) as in the source file
    replacements = [
        # Target 1: userSearchAttributes.add("uSNChanged") and "modifytimestamp"
        (
            '\t\tuserSearchAttributes.add("uSNChanged");\n'
            '\t\tuserSearchAttributes.add("modifytimestamp");',
            '\t\tif (config.isDeltaSyncEnabled()) {\n'
            '\t\t\tuserSearchAttributes.add("uSNChanged");\n'
            '\t\t\tuserSearchAttributes.add("modifytimestamp");\n'
            '\t\t}'
        ),
        # Target 2: groupSearchAttributes.add("uSNChanged") and "modifytimestamp"
        (
            '\t\tgroupSearchAttributes.add("uSNChanged");\n'
            '\t\tgroupSearchAttributes.add("modifytimestamp");',
            '\t\tif (config.isDeltaSyncEnabled()) {\n'
            '\t\t\tgroupSearchAttributes.add("uSNChanged");\n'
            '\t\t\tgroupSearchAttributes.add("modifytimestamp");\n'
            '\t\t}'
        ),
        # Target 3: extendedUserSearchFilter
        (
            '\t\t\textendedUserSearchFilter = "(objectclass=" + userObjectClass + ")(|(uSNChanged>=" + deltaSyncUserTime + ")(modifyTimestamp>=" + deltaSyncUserTimeStamp + "Z))";',
            '\t\t\tif (config.isDeltaSyncEnabled()) {\n'
            '\t\t\t\textendedUserSearchFilter = "(objectclass=" + userObjectClass + ")(|(uSNChanged>=" + deltaSyncUserTime + ")(modifyTimestamp>=" + deltaSyncUserTimeStamp + "Z))";\n'
            '\t\t\t} else {\n'
            '\t\t\t\textendedUserSearchFilter = "(objectclass=" + userObjectClass + ")";\n'
            '\t\t\t}'
        ),
        # Target 4: extendedAllGroupsSearchFilter (note double space after "(&")
        (
            '\t\t\textendedAllGroupsSearchFilter = "(&"  + extendedGroupSearchFilter + "(|(uSNChanged>=" + deltaSyncGroupTime + ")(modifyTimestamp>=" + deltaSyncGroupTimeStamp + "Z)))";',
            '\t\t\tif (config.isDeltaSyncEnabled()) {\n'
            '\t\t\t\textendedAllGroupsSearchFilter = "(&"  + extendedGroupSearchFilter + "(|(uSNChanged>=" + deltaSyncGroupTime + ")(modifyTimestamp>=" + deltaSyncGroupTimeStamp + "Z)))";\n'
            '\t\t\t} else {\n'
            '\t\t\t\textendedAllGroupsSearchFilter = extendedGroupSearchFilter;\n'
            '\t\t\t}'
        )
    ]

    for i, (target, replacement) in enumerate(replacements, 1):
        if replacement in content:
            print(f"Target {i} is already patched in {filepath}.")
            continue
        if target not in content:
            print(f"Error: Target {i} not found in {filepath}!")
            sys.exit(1)
        content = content.replace(target, replacement)

    with open(filepath, 'w') as f:
        f.write(content)

    print("Successfully patched LdapUserGroupBuilder.java!")

if __name__ == '__main__':
    main()
