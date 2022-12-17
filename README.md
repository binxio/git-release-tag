# git release tag
semantic versioning support for components in git repositories.

With the advent of continuous integration and continuous delivery, every commit to the source code repository delivers 
a new version of the software. The git source code repository system uses a 40 character long revision number, which
very accurately point at a specific version of the source code. However, these revision number are hard to read
for humans. This tool allows you to combine the best of both worlds: human readable version numbers while still being
able to uniquely identify a specific commit of the source code.

## How do I use this?
First you initialize the release configuration as follows:

```bash
git-release-tag initialize --initial-release 1.0.0 --tag-prefix v .
>>INFO: commit changes to .release in .
>>INFO: release 1.0.0 of . tagged by v1.0.0
```
This will add a file  called `.release` to the repository. It contains both the release and tag of the component
and place the tag. 

Now you can show the current version of the source code:

```bash
git-release-tag show 
>> 1.0.0
``` 
If you have outstanding changes in your workspace, the version is appended with the first 8 digits of the git revision number and
  `dirty`:
```bash
git-release-tag show
>> 1.0.0-81aca04e-dirty
```

If you commit changes to the repository, the version just shows the commit indicating a new version of the component

```bash
git-release-tag show
>> 1.0.0-63a8d99
```


## bumping the version
If you want to release the latest commit as a new version, type:
```bash
git-release-tag bump  --level patch 
>> INFO: commit changes to .release in .
>> INFO: release 1.0.1 of . tagged by v1.0.1
```
If there are no changes since the last version. bump with not change anything:
```bash
git-release-tag bump  --level patch  
>>INFO: . has no changes since 1.1.1.
```

## multiple components in a single repository
If you have multiple components in a single repository, initialize the repository as follows:

```bash
git-release-tag initialize --initial-release 1.0.0 ui backend .
>> INFO: commit changes to .release in ui
>> INFO: release 1.0.0 of ui tagged by ui-1.0.0
>> INFO: commit changes to .release in backend
>> INFO: release 1.0.0 of backend tagged by backend-1.0.0
>> INFO: commit changes to .release in .
>> INFO: release 1.0.0 of . tagged by api-1.0.0
```

When you want to release a new version of the component, type:
```bash
git-release-tag bump --recursive --level patch . 
>> INFO: commit changes to .release in ./ui
>> INFO: release 1.0.1 of ./ui tagged by ui-1.0.1
>> INFO: ./backend has no changes since 1.0.0.
>> INFO: commit changes to .release in .
>> INFO: release 1.0.1 of . tagged by api-1.0.1
```
As you can see, the ui now has version 1.0.1, the backend version is unchanged and the application  
has bumped to 1.0.1  too, because of the changes to the ui.

## dependencies between multiple components in a single repository
When you need to bump the version of a component when there are changes in other components in the
same repository, specify the dependency in the field `tag_on_changes_in` in the .release file.

So let's say that the UI always has to change when the api changes, change the .release as follows:

```
release=1.0.1
tag=ui-1.0.1
tag_on_changes_in=../api
```
Now, when there are changes in the ../api directory with respect to the tag in the ui directory,
a new release will be created.


## validating your configuration
As tags are not part of the commit, it sometimes happens that somebody forgets to push the tags along with the
commits. To validate the integrity of your release configuration, type:

```bash
git-release-tag validate --recursive .
>> INFO: ok
```
It reports an error if the configuration:
- references tags which are not in the repository.
- use the same tag for different components.

## including the current version in your application
To include the version of the release in the source code you can add a pre-tag-command to your configuration. This
is a command that is executed before the changes are committed.

```bash
git-release-tag initialize \
    --initial-release 1.0.0 \
    --tag-prefix v \
    --pre-tag-command 'sed -i "" -e "s/version=.*/version=\"@@RELEASE@@\",/g" setup.py' \
    .
>> INFO: commit changes to .release, setup.py in .
>> INFO: release 1.0.0 of . tagged by v1.0.0
```

The content of setup.py now reflects the released version and is included in the commit:
```bash
grep version= setup.py
>> version="1.0.0",
```

## installing the utility
To install the utility, type:

```bash
pip install git-release-tag
```
 
## inspired by native git describe
If you use a single git repository for each deliverable that you produce in the build process, you may use
`git-describe` instead. How does it work? Well you create a tag on a particular commit, and then type:

```bash
git tag 1.0.0
git describe --tags --dirty
>> 1.0.0
```
If you add something to the repository, it will append the number of commits since the tag and first 8 digits of the
revision number:
```bash
git describe --tags --dirty
>> 1.0.0-1-g6123dd2
```
If you have uncommited changes in the staging area, it will append `dirty` to it:
```bash
git describe --tags --dirty
>> 1.0.0-1-g6123dd2-dirty
```
If you commit your changes and place a new tag it show a clean tag again. git-describe does not work for the situation
where you have multiple artifacts in a single repository.
