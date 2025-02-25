CC  = g++ -O0

#PROG := solver
#OS := $(shell uname -s)

SYSTEM     = x86-64_linux
LIBFORMAT  = static_pic
CPLEX_ROOT_DIR= /opt/ibm/ILOG/CPLEX_Studio2211
CPLEXDIR = $(CPLEX_ROOT_DIR)/cplex
CONCERTDIR = $(CPLEX_ROOT_DIR)/concert
CPLEXLIBDIR   = $(CPLEXDIR)/../lib/$(SYSTEM)/$(LIBFORMAT)
CONCERTLIBDIR = $(CONCERTDIR)/../lib/$(SYSTEM)/$(LIBFORMAT)
INCLUDES += -I$(ABCSRC)/src -I$(CPLEXDIR) -I$(CONCERTDIR)

INCLUDESCPP += -I$(CONCERTDIR)


CCOPT = -m64 -O -fPIC -fno-strict-aliasing -fexceptions -DNDEBUG -DIL_STD

CPLEXBINDIR   = $(CPLEXDIR)/bin/$(BINDIST)
CPLEXLIBDIR   = $(CPLEXDIR)/lib/$(SYSTEM)/$(LIBFORMAT)
CONCERTLIBDIR = $(CONCERTDIR)/lib/$(SYSTEM)/$(LIBFORMAT)

CCLNDIRS  = -L$(CPLEXLIBDIR) -L$(CONCERTLIBDIR)
CLNDIRS   = -L$(CPLEXLIBDIR)
CCLNFLAGS = -L$(CPLEXLIBDIR) -lilocplex -lcplex -L$(CONCERTLIBDIR) -lconcert -lm -lpthread -ldl

all:     solver

CONCERTINCDIR = $(CONCERTDIR)/include
CPLEXINCDIR   = $(CPLEXDIR)/include

CCFLAGS = $(CCOPT) -I$(CPLEXINCDIR) -I$(CONCERTINCDIR)

clean : \
	/bin/rm -rf *.o *~ *.class solver \
	/bin/rm -rf *.mps *.ord *.sos *.lp *.sav *.net *.msg *.log *.clp

solver: solve.o
	$(CC) $(CCFLAGS) $(CCLNDIRS) -o solve solve.o $(CCLNFLAGS)
solve.o: solve.cpp
	$(CC) -c $(CCFLAGS) solve.cpp -o solve.o


