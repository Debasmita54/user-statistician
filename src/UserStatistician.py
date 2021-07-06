#!/usr/bin/env python3
#
# user-statistician: Github action for generating a user stats card
# 
# Copyright (c) 2021 Vincent A Cicirello
# https://www.cicirello.org/
#
# MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from Statistician import Statistician
from Colors import colorMapping
from StatsImageGenerator import StatsImageGenerator
import sys
import os
import subprocess

def writeImageToFile(filename, image, failOnError) :
    """Writes the image to a file, creating any
    missing directories from the path.

    Keyword arguments:
    filename - The filename for the image, with complete path.
    image - A string containing the image.
    failOnError - If True, the workflow will fail if there is an error
        writing the image to a file; and if False, this action will quietly
        exit with no error code. In either case, an error message will be
        logged to the console.
    """
    # Since we're running in a docker container, everything runs
    # as root. We need this umask call so we'll have write permissions
    # once the action finished and we're outside the container again.
    os.umask(0)
    # Create the directory if it doesn't exist.
    os.makedirs(os.path.dirname(filename), exist_ok=True, mode=0o777)
    try:
        # Write the image to a file
        with open(filename, "w") as file:
            file.write(image)
    except IOError:
        print("Error: An error occurred while writing the image to a file.")
        print("::set-output name=exit-code::4")
        exit(4 if failOnError else 0)

def executeCommand(arguments) :
    """Execute a subprocess and return result.

    Keyword arguments:
    arguments - The arguments for the command.
    """
    result = subprocess.run(
        arguments,
        stdout=subprocess.PIPE,
        universal_newlines=True
        ).stdout.strip()
    return result

def commitAndPush(filename, name, login) :
    """Commits and pushes the image.

    Keyword arguments:
    filename - The path to the image.
    name - The user's name.
    login - The user's login id.
    """
    # Make sure this isn't being run during a pull-request.
    result = executCommand(["git", "symbolic-ref", "-q", "HEAD"])
    if result == "0" :
        # Check if the image changed
        result = executeCommand(["git", "diff", "--exit-code", filename])
        if result == "1" :
            # Commit and push
            executeCommand(["git", "config", "--global", "user.name", name])
            executeCommand(["git", "config", "--global",
                            "user.email", login + '@users.noreply.github.com'])
            executeCommand(["git", "add", filename])
            executeCommand(["git", "commit", "-m",
                            "Automated change by [cicirello/user-statistician](https://github.com/cicirello/user-statistician)"])
            executeCommand(["git", "push"])


if __name__ == "__main__" :

    imageFilenameWithPath = sys.argv[1].strip()
    
    includeTitle = sys.argv[2].strip().lower() == "true"
    
    customTitle = sys.argv[3].strip()
    if len(customTitle) == 0 or not includeTitle :
        customTitle = None
        
    colors = sys.argv[4].strip().replace(",", " ").split()
    if len(colors) == 1 and colors[0] in colorMapping :
        # get theme colors
        colors = colorMapping[colors[0]]
    elif len(colors) < 4 :
        # default to light theme if invalid number of colors passed
        colors = colorMapping["light"]
    else :
        colors = { "bg" : colors[0],
                "border" : colors[1],
                "icons" : colors[2],
                "title" : colors[3],
                "text" : colors[4] if len(colors) > 4 else colors[3]
            }

    exclude = set(sys.argv[5].strip().replace(",", " ").split())

    failOnError = sys.argv[6].strip().lower() == "true"
    
    stats = Statistician(failOnError)
    generator = StatsImageGenerator(stats, colors)
    image = generator.generateImage(includeTitle, customTitle, exclude)
    writeImageToFile(imageFilenameWithPath, image, failOnError)
    
    print("::set-output name=exit-code::0")
    
