# Enc-1
idea by Annorphede.
====================================

REQUIREMENTS:
1. python 3.11.0 or higher;
2. external lib: pillow, cryptography.

====================================

Features:
   1. encrypts a string of engish letters into a 9-pixel wide png, using a cipher 
                                                                  -- main_no_salt.py

   2.generate ciphers using time salt
                                                                  -- salt.py
                                                                  
====================================

How to run? :
  0. create the following folders in the main folder: /ans ; /enc_wrapped ; /keys ; /unwraps
  1. install 「pillow, cryptography」: pip install pillow cryptography
     (for great mac users: pip3 install pillow cryptography)
     pillow deals with the photos
  2. go to the directory where you downloaded these sucking codes:
     4Windows: ~ sorry, idk :-O ~
     4macOS  : 「cd ~/"Your directory"」
               and the terminal says: blablabla (wish there are no errors). then:
               「python3 main_no_salt.py」

=======================================================

Notice:
1. all the console outputs are written in chinese, and if you want to read it more smoothly, you can learn chinese or modify the source code by yourself.
2. never use this for real encrypting, because, MOST POSSIBLY YOU CAN'T FIGURE OUT A WAY TO SAFELY TRANSMIT YOUR CIPHER, which can be deadly.
3. run env.py to wrap the file as a .enc file, using cipher photo or a password.
4. ENJOY :)
