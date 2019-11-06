#!/usr/bin/env python

import vk
import subprocess
import os
import sys
import time
from termcolor import colored
import argparse
from terminaltables import SingleTable as T

# not mutable by arguments
API_VERSION = '5.103'
REQUEST_DELAY = 0.3
TOKEN_FILE = 'token.txt'

# mutable by arguments
POST_COUNT = 10
KEYWORD = 'добавь'
GROUP_COUNT = 50
OFFSET = 0

COMMANDS = {'next' : '/next', 
            'exit' : '/exit'
            }

HELP_MESSAGE ='''Usage: ./make_friends.py [OPTIONS]

  --add		Only accept all requests to friends
  --help	Print this message
'''

MESSAGE = 'Ребят, добавляйтесь, приму всех инфа 100%)))'

def vk_get_api():    
    def get_token(file):
        with open(file, "r") as f:
            return f.readline()
            
    token = get_token(TOKEN_FILE)
    session = vk.Session(access_token=token);
    return vk.API(session, v=API_VERSION)

def vk_get_groups(api, keyword, group_count, offset):
    groups = api.groups.search(q=keyword, count=group_count, offset=offset)['items']
    time.sleep(REQUEST_DELAY)
    
    print(colored('Received %s groups on request "%s"' % (len(groups) if groups else 0, keyword), 'yellow', attrs=['bold']))
    print(colored('Removing private groups...', 'yellow', attrs=['bold']))
    ids = [i['id'] for i in groups]
    if not ids:
        print(colored('No groups found', 'yellow', attrs=['bold']))
        return
    groups = api.groups.getById(group_ids=ids, fields='can_post,members_count')    
    time.sleep(REQUEST_DELAY)
    
    # two items are required by algorithm, others are optional
    groups = [(-i.get('id'), i.get('can_post'), i.get('members_count'), i.get('name'), 'https://vk.com/' + i.get('screen_name')) for i in groups if not i['is_closed']]
    print(colored('Groups left: %s' % len(groups), 'yellow', attrs=['bold']))
    return groups

def vk_get_posts(api, group, post_count):
    if not post_count:
        return None
        
    posts = api.wall.get(owner_id=group[0], count=post_count)['items']
    time.sleep(REQUEST_DELAY)
    
    print(colored('%s posts founded in group %s' % (len(posts), group[4]), 'yellow', attrs=['bold']))
    print(colored('Removing posts that prohibits commenting...', 'yellow', attrs=['bold']))
    posts = [(i['id'], '%s?w=wall%s_%s' % (group[4], group[0], i['id'])) for i in posts if i['comments']['can_post']]
    print(colored('Posts left: %s' % len(posts), 'yellow', attrs=['bold']))
    return posts
    
def vk_spam(api, groups, post_count, msg):   
    count = 0
    for i in groups:                
        continue_on = False
        count += 1
        print()
        print(colored(' %s/%s' % (count, len(groups)), 'grey', 'on_white'))
        print(colored(' -> Group %s' % i[4], 'white', attrs=['bold']))
        print(colored(' -> %s members\n' % i[2], 'white', attrs=['bold']))
        
        posts = vk_get_posts(api, i, post_count)
        if posts:            
            count_posts = 0
            for j in posts:
                count_posts += 1
                print(colored(' %s/%s' % (count_posts, len(posts)), 'grey', 'on_white'))
                print(colored(' -> Post %s' % j[1], 'white', attrs=['bold']))
        
                cmd = vk_handle_captcha(lambda key, sid: \
                    api.wall.createComment( \
                        owner_id=i[0], post_id=j[0], message=msg, \
                        captcha_sid=sid, captcha_key=key)['comment_id'], \
                        (' -> Comment %s_r' % j[1]) + '%s created')
                if cmd == COMMANDS['next']:
                    continue_on = True
                    break;
                   
        if continue_on:
            continue
            
        if i[1]: # can post
            vk_handle_captcha(lambda key, sid: \
                api.wall.post( \
                    owner_id=i[0], message=msg, \
                    captcha_sid=sid, captcha_key=key)['post_id'], \
                    (' -> Post %s?w=wall%s_' % (i[4], i[0])) + '%s created')

def vk_add_friends(api):
    requests = api.friends.getRequests()['items']
    time.sleep(REQUEST_DELAY)
    for i in requests:
        api.friends.add(user_id=i)        
        time.sleep(REQUEST_DELAY)
        print(colored('Friend https://vk.com/id%s added' % i, 'yellow', attrs=['bold']))

def vk_handle_captcha(f, msg):
    key, sid = 0, 0
    while True:
        try:
            value = f(key, sid)
            time.sleep(REQUEST_DELAY)
            print(colored(msg % value, 'green', attrs=['bold']))
            break
        except vk.exceptions.VkAPIError as e:
            print(colored('ERROR: %s' % e.message, 'white', 'on_red'))
            if e.is_captcha_needed():               
                key, sid = solve_captcha(e)
                if handle_captcha_command(key):
                    return key
            else:
                time.sleep(REQUEST_DELAY)
                again = input('Try again? [Y/n] ')
                if again.lower() == 'y':
                    continue
                else:
                    if handle_captcha_command(again):
                        return again
                    break
            time.sleep(REQUEST_DELAY)

def handle_captcha_command(cmd):
    if cmd == COMMANDS['exit']:
        sys.exit(0)
    elif cmd == COMMANDS['next']:
        return cmd
        
def solve_captcha(e):
    print(colored('Captcha image: %s' % e.captcha_img, 'red', attrs=['bold']))
    proc = subprocess.Popen(['feh', e.captcha_img], shell=False, start_new_session=True)
    key = input(colored('Enter captcha: ', 'red', attrs=['bold']))
    proc.terminate()
    return key, e.captcha_sid

def print_groups(groups):    
    table = [('n', 'name', 'id', 'members')]
    for i in range(len(groups) if groups else 0):
        table.append((
            colored('%s' % (i+1), 'white', attrs=['bold']),
            colored(groups[i][3], 'green', attrs=['bold']),
            colored('%s' % -groups[i][0], 'white', attrs=['bold']),
            colored('%s' % groups[i][2], 'white', attrs=['bold'])))
    print(T(table).table)
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', action='store_true', help='only accept friend requests')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s 0.1.0') 
    parser.add_argument('-l', '--list-groups', action='store_true', help='print list of groups found')
    parser.add_argument('-k', '--keyword', default=KEYWORD, dest='KEYWORD', help='set keyword for searching groups')
    parser.add_argument('-m', '--message', default=MESSAGE, dest='MESSAGE', help='set default message to post and comment')
    parser.add_argument('-g', '--group-count', default=GROUP_COUNT, dest='GROUP_COUNT', type=int, help='set maximum number of groups')    
    parser.add_argument('-p', '--post-count', default=POST_COUNT, dest='POST_COUNT', type=int, help='set number of posts for commenting in one group')
    parser.add_argument('-o', '--offset', default=OFFSET, dest='OFFSET', type=int, help='set offset of group list')
    args = parser.parse_args()
    
    api = vk_get_api()
    
    if args.add:
        vk_add_friends(api)
    elif args.list_groups:
        print_groups(vk_get_groups(api, args.KEYWORD, args.GROUP_COUNT, args.OFFSET))
    else:
        groups = vk_get_groups(api, args.KEYWORD, args.GROUP_COUNT, args.OFFSET)
        if not groups:
            sys.exit(0)
        while True:
            vk_spam(api, groups, args.POST_COUNT, args.MESSAGE)
            vk_add_friends(api)