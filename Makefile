CC=g++
CFLAGS=-fPIC -std=c++17 -O2
NAME=score_guess_opt
SOURCES=$(NAME).cpp

all: 
	$(CC) $(CFLAGS) -shared -o $(NAME).so $(SOURCES)

clean:
	rm -f $(NAME).so
