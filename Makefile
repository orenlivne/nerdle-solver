CC=g++
CFLAGS=-fPIC
NAME=score_guess_opt
SOURCES=$(NAME).cpp

all: 
	$(CC) $(CFLAGS) -shared -o $(NAME).so $(SOURCES)

clean:
	rm -f $(NAME).so
