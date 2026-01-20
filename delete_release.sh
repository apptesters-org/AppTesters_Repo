# [INFO] to run this... cd to the directory and run "./delete_release.sh" but before that do "chmod +x delete_release.sh"
#and then provide dates like this: 05-03-2025 16-02-2025 02-03-2025 12-02-2025 to delete the releases. [/INFO]

#!/bin/bash

# Configuration
owner="apptesters-org"
repo="AppTesters_Repo"

echo "--- Fetching ALL releases for $owner/$repo ---"

# 1. Fetch ALL release tags using gh api with pagination
all_releases=$(gh api "repos/$owner/$repo/releases" --paginate --jq '.[].tag_name')

if [ -z "$all_releases" ]; then
    echo "No releases found."
    exit 0
fi

# 2. Display releases
echo "Found the following releases:"
echo "----------------------------"
echo "$all_releases"
echo "----------------------------"
echo ""

# 3. Ask user for input
echo "Paste the tags you want to delete (separated by spaces):"
read -p "Tags to delete: " -a target_tags

if [ ${#target_tags[@]} -eq 0 ]; then
    echo "No tags entered."
    exit 0
fi

echo ""
echo "Starting deletion..."

# 4. Loop and delete WITHOUT asking for confirmation
for tag in "${target_tags[@]}"; do
    if [ -z "$tag" ]; then continue; fi
    
    echo "Deleting $tag..."
    
    # --yes : Skips the "y/n" prompt
    # --cleanup-tag : Deletes the git tag as well (removes the "tag still remains" warning)
    gh release delete "$tag" --repo "$owner/$repo" --yes --cleanup-tag
done

echo "Done."