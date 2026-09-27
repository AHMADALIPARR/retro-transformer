       IDENTIFICATION DIVISION.
       PROGRAM-ID. FILEIO.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT PAY-FILE ASSIGN TO 'PAY.DAT'.
       DATA DIVISION.
       FILE SECTION.
       FD PAY-FILE.
       01 PAY-REC.
           05 F-NAME PIC X(20).
           05 F-AMT  PIC 9(6)V99.
       WORKING-STORAGE SECTION.
       01 WS-FLAGS.
           05 WS-EOF PIC X VALUE 'N'.
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           OPEN INPUT PAY-FILE.
           PERFORM READ-LOOP UNTIL WS-EOF = 'Y'.
           CLOSE PAY-FILE.
           STOP RUN.
       READ-LOOP.
           READ PAY-FILE INTO PAY-REC
               AT END MOVE 'Y' TO WS-EOF
           END-READ.
           IF WS-EOF = 'N'
               DISPLAY F-NAME ' ' F-AMT
           END-IF.
