#!/usr/bin/env python
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: ./update_token [URL]')
        sys.exit(1)
        
    beg = sys.argv[1].find('#access_token=') + len('#access_token=')
    end = sys.argv[1].find('&', beg)
    token = sys.argv[1][beg:end]
    with open('token.txt', 'w+') as f:
        f.write(token)
