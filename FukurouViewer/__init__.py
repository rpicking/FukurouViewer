import sys
from FukurouViewer import program, threads

app = program.Program(sys.argv)
threads.setup()
app.setup()