// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(READ)

@KBD
D=M

@FILL_BLACK
D;JNE

@color
M=0

@FILL
0;JMP

(FILL_BLACK)
@0
D=!A

@color
M=D

(FILL)
@8192
D=A
@i
M=D

@SCREEN
D=A

@addr
M=D

(CYCLE)
@color
D=M

@addr
A=M
M=D

@addr
M=M+1

@i
MD=M-1

@READ
D;JEQ

@CYCLE
0;JMP




