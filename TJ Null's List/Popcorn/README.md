## Popcorn

https://app.hackthebox.com/machines/popcorn

This machine has been resolved on OSCP machines: [Popcorn](https://github.com/b1d0ws/OSCP/tree/main/TJ%20Null's%20List/Linux%20Boxes/Popcorn)

Here you will find the script that automated the arbitrary file upload vulnerability that occurs on this machine.

We need to:
* Login in;
* Upload a new torrent;
* Edit torrent and upload image bypassing Content-Type validation using something like "image/jpg"

For some reason I was unable to upload the torrent, so this process needs to be done manually before running the script.
