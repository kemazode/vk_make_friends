#!/usr/bin/env python

import vk
import subprocess
import os
import sys
import time
from termcolor import colored

API_VERSION = '5.103'
REQUEST_DELAY = 0.3
TOKEN_FILE = 'token.txt'
POSTS_COUNT = 10
KEYWORD = 'добавь'
GROUP_COUNT = 50

COMMANDS = {'next' : '/next', 
            'nextgroup' : '/nextgroup',
            'exit' : '/exit'
            }

MESSAGE = 'Ребят, добавляйтесь, приму всех инфа 100%)))'

def vk_get_api():    
    def get_token(file):
        with open(file, "r") as f:
            return f.readline()
            
    token = get_token(TOKEN_FILE)
    session = vk.Session(access_token=token);
    return vk.API(session, v=API_VERSION)

def vk_get_groups(api):
    groups = api.groups.search(q=KEYWORD, count=GROUP_COUNT)['items']
    time.sleep(REQUEST_DELAY)
    
    print(colored('Received %s groups on request "%s"' % (len(groups), KEYWORD), 'yellow', attrs=['bold']))
    print(colored('Removing private groups...', 'yellow', attrs=['bold']))
    ids = [i['id'] for i in groups]
    
    groups = api.groups.getById(group_ids=ids, fields='can_post,members_count')    
    time.sleep(REQUEST_DELAY)
    
    groups = [(-i['id'], i['can_post'], i['members_count']) for i in groups if not i['is_closed']]
    print(colored('Groups left: %s' % len(groups), 'yellow', attrs=['bold']))
    return groups

def vk_get_posts(api, group_id):
    posts = api.wall.get(owner_id=group_id, count=POSTS_COUNT)['items']
    time.sleep(REQUEST_DELAY)
    
    print(colored('%s posts founded in group %s' % (len(posts), -group_id), 'yellow', attrs=['bold']))
    print(colored('Removing posts that prohibits commenting...', 'yellow', attrs=['bold']))
    posts = [i['id'] for i in posts if i['comments']['can_post']]
    print(colored('Posts left: %s' % len(posts), 'yellow', attrs=['bold']))
    return posts
    
def vk_spam(api, groups):   
    count = 0
    continue_on = False
    for i in groups:                
        count += 1
        print()
        print(colored(' %s/%s' % (count, len(groups)), 'grey', 'on_white'))
        print(colored(' -> Group %s' % -i[0], 'white', attrs=['bold']))
        print(colored(' -> %s members\n' % i[2], 'white', attrs=['bold']))
        
        posts = vk_get_posts(api, i[0])
        for j in posts:
            cmd = vk_handle_captcha(lambda key, sid: \
                api.wall.createComment( \
                    owner_id=i[0], post_id=j, message=MESSAGE, \
                    captcha_sid=sid, captcha_key=key)['comment_id'], \
                    'Comment %s is added')
            if cmd == COMMANDS['nextgroup']:
                continue_on = True
                break;
                   
        if continue_on:
            continue
            
        if i[1]: # can post
            vk_handle_captcha(lambda key, sid: \
                api.wall.post( \
                    owner_id=i[0], message=MESSAGE, \
                    captcha_sid=sid, captcha_key=key)['post_id'], \
                    'Post %s is created')

def vk_add_friends(api):
    requests = api.friends.getRequests()['items']
    time.sleep(REQUEST_DELAY)
    for i in requests:
        api.friends.add(user_id=i)        
        time.sleep(REQUEST_DELAY)
        print(colored('Friend %s added' % i, 'yellow', attrs=['bold']))

def vk_handle_captcha(f, msg):
    key, sid = 0, 0
    captcha_solved = False
    while not captcha_solved:
        try:
            value = f(key, sid)
            time.sleep(REQUEST_DELAY)
            print(colored(msg % value, 'green', attrs=['bold']))
        except vk.exceptions.VkAPIError as e:
            print(colored('ERROR: %s' % e.message, 'white', 'on_red'))
            if e.is_captcha_needed():               
                key, sid = solve_captcha(e)
                if key == COMMANDS['exit']:
                    sys.exit(0)
                elif key in COMMANDS.values():
                    return key
            else:
                break
            time.sleep(REQUEST_DELAY)
        
def solve_captcha(e):
    print(colored('Captcha image: %s' % e.captcha_img, 'red', attrs=['bold']))
    proc = subprocess.Popen(['feh', e.captcha_img], shell=False, start_new_session=True)
    key = input(colored('Enter captcha: ', 'red', attrs=['bold']))
    proc.terminate()
    return key, e.captcha_sid

if __name__ == '__main__':
    api = vk_get_api()
    groups = vk_get_groups(api)
    while True:
        vk_spam(api, groups)
        vk_add_friends(api)