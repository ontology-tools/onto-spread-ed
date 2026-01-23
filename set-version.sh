#!/bin/bash

# Set the version for all packages and plugins

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

NEW_VERSION=$1

# Update version in all pyproject.toml files
find packages plugins -name pyproject.toml -exec bash -c 'uv version --project $(dirname $0) $1' {} $NEW_VERSION \;

#Update version in all package.json files
find packages plugins -name package.json -exec bash -c 'printf "%s %s => %s\n" $(basename $(dirname $0)) $(cat $0 | jq ".version") $(npm version --prefix $(dirname $0) $1 --no-git-tag-version)' {} $NEW_VERSION \;

# function update_in_pyproject_toml() {
#     local file_path=$1
#     local new_version=$2
#     sed -i -E "s/\"ose-(.*)=.*\"/\"ose\1=$new_version\"/" "$file_path"
# }
# export -f update_in_pyproject_toml

# Update all dependencies to the new version
find packages plugins -name pyproject.toml -exec bash -c 'sed -i -E "s/\"ose-(.*)=.*\"/\"ose-\1=$1\"/" $0' {} $NEW_VERSION \;
