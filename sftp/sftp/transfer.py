#!/usr/bin/env python3

import os
import sys
from getpass import getpass
from ftplib import FTP
import paramiko

def get_input(prompt):
    return input(prompt).strip()

def get_source_details():
    print("Source FTP/SFTP Details:")
    source = {
        'host': 'localhost',  # Assuming the source is on the same machine
        'user': get_input("Enter source username: "),
        'pass': getpass("Enter source password: "),
        'port': int(get_input("Enter source port (21 for FTP, 22 for SFTP): ")),
        'path': get_input("Enter the full path of the file or folder to transfer: ")
    }
    return source

def get_dest_details():
    print("\nDestination FTP/SFTP Details:")
    dest = {
        'host': get_input("Enter destination host: "),
        'user': get_input("Enter destination username: "),
        'pass': getpass("Enter destination password: "),
        'port': int(get_input("Enter destination port (21 for FTP, 22 for SFTP): ")),
        'path': get_input("Enter the destination path: ")
    }
    return dest

def transfer_ftp(source, dest, is_file):
    with FTP() as ftp_source:
        ftp_source.connect(source['host'], source['port'])
        ftp_source.login(source['user'], source['pass'])
        
        with FTP() as ftp_dest:
            ftp_dest.connect(dest['host'], dest['port'])
            ftp_dest.login(dest['user'], dest['pass'])
            
            if is_file:
                # Transfer single file
                with open(source['path'], 'rb') as local_file:
                    ftp_dest.storbinary(f'STOR {os.path.join(dest["path"], os.path.basename(source["path"]))}', local_file)
                print(f"File {source['path']} transferred successfully.")
            else:
                # Transfer entire folder
                for root, dirs, files in os.walk(source['path']):
                    for filename in files:
                        local_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(local_path, source['path'])
                        remote_path = os.path.join(dest['path'], relative_path)
                        remote_dir = os.path.dirname(remote_path)
                        
                        # Create remote directories if they don't exist
                        try:
                            ftp_dest.mkd(remote_dir)
                        except:
                            pass
                        
                        with open(local_path, 'rb') as local_file:
                            ftp_dest.storbinary(f'STOR {remote_path}', local_file)
                        print(f"File {local_path} transferred successfully.")

def transfer_sftp(source, dest, is_file):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(source['host'], port=source['port'], username=source['user'], password=source['pass'])
        
        with ssh.open_sftp() as sftp_source, paramiko.SSHClient() as ssh_dest:
            ssh_dest.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_dest.connect(dest['host'], port=dest['port'], username=dest['user'], password=dest['pass'])
            
            with ssh_dest.open_sftp() as sftp_dest:
                if is_file:
                    # Transfer single file
                    sftp_dest.put(source['path'], os.path.join(dest['path'], os.path.basename(source['path'])))
                    print(f"File {source['path']} transferred successfully.")
                else:
                    # Transfer entire folder
                    for root, dirs, files in os.walk(source['path']):
                        for filename in files:
                            local_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(local_path, source['path'])
                            remote_path = os.path.join(dest['path'], relative_path)
                            remote_dir = os.path.dirname(remote_path)
                            
                            # Create remote directories if they don't exist
                            try:
                                sftp_dest.stat(remote_dir)
                            except FileNotFoundError:
                                sftp_dest.mkdir(remote_dir)
                            
                            sftp_dest.put(local_path, remote_path)
                            print(f"File {local_path} transferred successfully.")

def main():
    source = get_source_details()
    dest = get_dest_details()
    
    is_file = os.path.isfile(source['path'])
    
    if source['port'] == 21 and dest['port'] == 21:
        transfer_ftp(source, dest, is_file)
    elif source['port'] == 22 and dest['port'] == 22:
        transfer_sftp(source, dest, is_file)
    else:
        print("Error: Both source and destination must use the same protocol (FTP or SFTP).")
        sys.exit(1)

if __name__ == "__main__":
    main()
