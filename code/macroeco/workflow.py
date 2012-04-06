#!/usr/bin/python

'''
Workflow manages the details of a reproducible workflow within the METE system.

Classes
-------
- Workflow: tracks the analysis & data requested, and any parameters needed.
- Parameters: Find, or ask for, and store the run names and parameters asked for by an analysis.

'''
import xml.etree.ElementTree as etree
import sys, os, logging
from matplotlib.mlab import csv2rec

__author__ = "Chloe Lewis"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = []
__license__ = None
__version__ = "0.5"
__maintainer__ = "Chloe Lewis"
__email__ = "chlewis@berkeley.edu"
__status__ = "Development"

paramfile = "parameters.xml"
logfile   = "logfile.txt"
loggername = "macroeco"



class Workflow:
    '''
    Manages the details of a reproducible workflow with macroeco scripts.
    Tracks which data set(s) are analyzed with which set(s) of parameters.

    Parameters
    ----------
    asklist : dictionary
              'parameter_name':'hint' describes the parameters needed.
              If not given, all parameters recorded in %s
              for the current scriptname will be available.

    Members
    -------
    script : string
             Name of script originating the workflow
    logger : logging.logger
             Also shareable with any module as logging.getLogger(%s)
    interactive : bool
             Whether the script can pause for user interaction
    runs   : dict
             If parameters are needed, sets of parameter values are named runs
    '''%(paramfile, loggername)

    def __init__(self, asklist={}):
        # Track output with the analysis name as running. Tidy up:
        sPath, sExt = os.path.splitext(sys.argv[0])
        self.script = os.path.split(sPath)[-1]


        # The rest of the arguments are the data files to analyze.
        self.datafiles = sys.argv[1:]
    
        self.data = {}
        for dfile in sys.argv[1:]:
            dname, dext = os.path.splitext(os.path.split(dfile)[-1])
            self.data[dname] = csv2rec(dfile)


        # Log everything to console; log dated INFO+ to file.
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s', datefmt='%H:%M:%S')
        self.logger = logging.getLogger(loggername)
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


        if len(sys.argv) < 2:
            self.logger.critical('Need a path to data.')
            sys.exit()

        #may need parameters, which may be in multiple runs
        try:
            self.runs = Parameters(self.script, asklist) #The asking stuff happens post-beta.
            self.interactive = self.runs.interactive
        except:
            self.interactive = False
            self.runs = None

            
        
    def single_datasets(self):
        '''
        Generator. For each dataset being analyzed:

        Yields
        ------
        datasetpath, outputID

        datasetpath : string
                      Full path to data to analyze
        outputID : string
                   Concatenates script and dataset identifiers
        '''
        if type(self.runs) == type(None):
            for df in self.datafiles:
                self.logger.debug(df)
                ID = '_'.join([self.script, _clean_name(df)])
                yield  df, ID
        else:
            for run in self.runs.params.keys():
                for df in self.datafiles:
                    ID = '_'.join([self.script, _clean_name(df), run])
                    yield  df, ID, self.runs.params[run]
                
    
    def all_datasets(self):
        '''
        Returns
        -------
        datasetpaths, outputID
        
        datasetpaths : list
                       List of complete paths to all datasets.

        outputID : string
                   Concatenates script and all dataset identifiers.
        '''
        datanames = map(_clean_name, self.datafiles)
        outputID = '_'.join([self.script]+datanames)
        if type(self.runs) == type(None):
            self.logger.debug('No params')
            yield self.datafiles, outputID
        else:
            self.logger.debug('Multiple params')
            for run in self.runs.params.keys():
                outputID = '_'.join([self.script]+datanames + [run])
                yield self.datafiles, outputID, self.runs.params[run]

        

    def make_map(self):
        pass

        
class AllEntities:
    def __getitem__(self, key):
        return key        

class Parameters:
    '''Parameter values for any analysis:
        asked for as a dictionary of name:helpstring,
        available as self.params, a dictionary of name:value and "run_name":runname,
        written to the current working directory in %s.
    Parameters also tracks the run name, interactivity, and multiplicity.

    If %s is not sufficient, a dialog-box asks the user for values.'''%(paramfile, paramfile)
    
    def __init__(self, scriptname, asklist={}):
        '''Builds a dictionary of dictionaries to satisfy the asklist.

        Outer dictionary names are run names; inner are parameter name:value pairs.

        Finds parameters in this order:

            If there are interactive runs in %s for this scriptname:
                open populated dialog, return results with run_name.

            If there are only noninteractive runs in %s:
                if they satisfy the asklist for this scriptname:
                    return parameters with run_names added.
                    

        The argument asklist is a dictionary of 'name':'helpstring'.
        Helpstrings should be short and explain what kind of value is needed, e.g., 
            string,
            value in a range,
            value from a list.'''%(paramfile, paramfile)

        assert type(asklist) == type({}) #TODO: Integration test
        self.interactive = None
        self.script = scriptname
        self.params = {}
        self.logger = logging.getLogger(loggername)
        

        self.read_from_xml(asklist)
        self.logger.debug('read parameters: %s'%str(self.params))
        if not self.is_asklist_fulfilled:
            self.logger.critical('Parameters missing from %s'%paramfile)
        return
        
        

        later='''        self.get_from_dialog(asklist)
        if self.is_asklist_fulfilled:
            self.write_to_xml()
            return
        
            else:
            raise Error #user wasn't helpful... TODO error type'''
         
    def read_from_xml(self, asklist):

        try:
            pf = open(paramfile,'r')
            pf.close()
        except IOError:
            self.logger.error('Could not open %s'%paramfile) #Note; can't write is also an IOError
            raise

        parser = etree.XMLParser() # Without this, parsing works in iPython, console, not script. ??
        parser.parser.UseForeignDTD(True)
        parser.entity = AllEntities()
        try:
            pml = etree.parse(paramfile, parser=parser).getroot() #Depends on cwd - #TODO integration test
        except etree.ParseError:
            self.logger.error('ParseError trying to read %s'%paramfile)
        except:
            self.logger.error(sys.exc_info()[0])
        runcount = 0
        if len(pml) > 0:
            for child in pml:
                # check if any of these match scriptname TODO: and version (later)
                if child.get('scriptname') == self.script:
                    analysis = child
                    if 'interactive' in child.attrib:
                        ia = child.get('interactive')
                        if ia == 'F' or ia == 'False' or ia == 'f' or ia == 'false':
                            self.interactive = False
                        else:
                            self.interactive = True
                    else:
                        self.interactive = False #TODO: consider the default.
                    if len(analysis) > 0:
                        for run in analysis.getchildren():
                            if 'name' in run.attrib:
                                current_run = run.get('name')
                            else:
                                current_run = 'autoname'+str(runcount)
                                runcount += 1
                            self.params[current_run] = {}
                            for elt in run.getchildren():
                                if elt.tag == 'param':
                                    self.params[current_run][elt.get('name')] = elt.get('value')
        else:
            self.logger.error("Need run entries in %s"%paramfile)

        # if none, *or* if interactive, put up dialog asking for values for all the params

        # on dialog OK, write out  -- replace run with same name (tricky!)

    def is_asklist_fulfilled(self):
        if not set(self.params.keys()).issubset(set.self.asklist.keys()):
            #some are missing
            self.missing = ['Later','gator']
            return False
        else:
            return True
            
def _clean_name(fp):
        return os.path.splitext(os.path.split(fp)[-1])[0]

