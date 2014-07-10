# -*- coding: utf-8 -*-

"""
    Interactive console
"""

__version__ = "$Id: interactive.py 352 2014-03-03 18:22:45Z campr $"

import sys
import getpass
import termcolor

def format_header(msg):
    return termcolor.colored(msg, color='green', attrs=['underline', 'bold'])

def format_prompt(msg):
    return termcolor.colored(msg, color='green', attrs=['bold'])

def format_error(msg):
    return termcolor.colored(msg, color='red', attrs=['bold'])

def input(prompt, allow_empty=False, type='unicode', default_value=None):
    if default_value is not None:
        default_value = str(default_value)
        prompt += ' (default value: %s):' % (default_value)

    prompt = format_prompt(prompt)

    while True:
        result = raw_input(prompt).decode(sys.stdin.encoding or 'utf-8')

        if len(result)==0:
            result = None

        if result is None:
            if allow_empty:
                return result
            else:
                # empty not allowed, use default value when given
                if default_value is not None:
                    result = default_value
                else:
                    continue

        if type=='int':
            try:
                result = int(result)
            except:
                continue
        elif type=='float':
            try:
                result = float(result)
            except:
                continue
        elif type=='bool':
            try:
                result = bool(int(result))
            except:
                continue
        elif type=='unicode':
            pass
        else:
            raise Exception("Unsupported type: %s" % (type))

        return result


def input_password(prompt):
    prompt = "  " + prompt
    prompt1 = prompt
    prompt2 = prompt + " (again):"

    while True:
        print format_prompt("Please provide password at least 6 characters long:")

        pw1 = getpass.getpass(prompt1).decode(sys.stdin.encoding or 'utf-8')
        pw2 = getpass.getpass(prompt2).decode(sys.stdin.encoding or 'utf-8')

        if len(pw1) < 6 :
            print format_error("Password must be at least 6 characters long!")
            continue

        if pw1 != pw2:
            print format_error("Passwords do not match!")
            continue

        return pw1