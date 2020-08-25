# @name: synth_sampler.py
# @description: Script to generate synthetic fair data
# @version: 1.0
# @date: 25-08-2020
# @author: Núria Queralt Rosinach
# @email: n.queralt_rosinach@lumc.nl

# This script is based on the WHO CODID-19 CRF RDF-wizard '../form2triples.py' adapted to python 3.8.

# TODO: run under python 3.8
"""Script to generate synthetic fair data"""

import rdflib, csv
from datetime import datetime
from rdflib import *
from os import listdir

var2class = {}
readfiles = []
onto = rdflib.Graph()
g = rdflib.Graph()
n = Namespace('http://purl.org/vodan/whocovid19crfsemdatamodel/')
DC = Namespace('http://purl.org/dc/elements/1.1/')
part_of = URIRef('http://purl.obolibrary.org/obo/BFO_0000050')
yes = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/C49488')
no = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/C49487')
unknown = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/C17998')
not_done = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/Not_done')
negative = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/Negative')
positive = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/Positive')
unit_label = URIRef('http://purl.obolibrary.org/obo/IAO_0000039')
site_id = 'EMPTY'

csv_path = './form/'
variable_path = './vars/'

onto.load('https://github.com/FAIRDataTeam/WHO-COVID-CRF/raw/master/WHO_COVID-19_Rapid_Version_CRF_Ontology.owl')

def YN2B(input):
    if input == 'Yes':
        return Literal('True', datatype=XSD.boolean)
    elif input == 'No':
        return Literal('False', datatype=XSD.boolean)
    else:
        return Literal('invalid input')

def YNU2subject(input):
    if input == 'Yes':
        return yes
    elif input == 'No':
        return no
    elif input == 'Unknown':
        return unknown


def PNN2subject(input):
    if input == 'Positive' or input == 'Postive': #Option 'Postive' due to error in form output
        return positive
    elif input == 'Negative':
        return negative
    elif input == 'Not Done':
        return not_done


def getPartOfClass(owl_class):
    result=[]
    superclasses = onto.transitive_objects(owl_class, RDFS.subClassOf)
    #superclasses = onto.objects(owl_class, RDFS.subClassOf)
    for superclass in superclasses:
        if (superclass, RDF.type, OWL.Restriction) in onto:
            if (superclass, OWL.onProperty, part_of) in onto:
                tussen = superclass
                for s, p, o in onto.triples((tussen, OWL.someValuesFrom, None)):
                    result.append(o)
    if len(result) == 0:
        print('no part of found for ' + owl_class.toPython())
        return('empty')
    elif len(result) == 1:
        return(result[0])
    else:
        return('more than 1 result')


def getUnit(question):
    superclasses = onto.transitive_objects(question, RDFS.subClassOf)
    for superclass in superclasses:
        if (superclass, RDF.type, OWL.Restriction) in onto:
            if (superclass, OWL.onProperty, unit_label) in onto:
                for s,p,o in onto.triples((superclass, OWL.hasValue, None)):
                    return(o)


def hasLOV(list_question):
    superclasses = onto.transitive_objects(list_question, RDFS.subClassOf)
    for superclass in superclasses:
        if isinstance(superclass, BNode):
            if onto.objects(superclass, OWL.onProperty).next() == n.has_value:
                #print(superclass)
                superpart = onto.objects(superclass, OWL.onClass)
                try:
                    lov = superpart.next()
                except StopIteration:
                        superpart = onto.objects(superclass, OWL.someValuesFrom)
                        try:
                            lov2 = superpart.next()
                        except StopIteration:
                            return None
                        return (lov2)
                return(lov)


#translate the variables in the form to the correct URI's, using config files
var_files = listdir(variable_path)
for file in var_files:
    if file[-4:] == '.csv':
        with open (variable_path + file) as translate_file:
            formreader = csv.reader(translate_file, delimiter=',')
            for row in formreader:
                if row[1] != '':
                    var2class[row[0]] = URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/' + row[1])


#Create the list of files to process, in the right order
files = listdir(csv_path)
for file in files:
    if file[:4] == 'New_':
        readfiles.append(file)
#first file to read is the one with the shortest name (base reports)
shortest = 1000
for file in readfiles:
    if len(file) < shortest:
        first_file = file
        shortest = len(first_file)
readfiles.remove(first_file)
readfiles.insert(0, first_file)
file_base_name = first_file[:(first_file.find('_export'))]

#second file to read is the one with the daily reports
for file in readfiles:
    if 'Daily_Case_Report_Form' in file:
        second_file = file
readfiles.remove(second_file)
readfiles.insert(1, second_file)


for csv_file in readfiles:
    print('Handling file: ' + csv_file)
    with open(csv_path + csv_file) as who_form:
    #with open('/Users/marc/Downloads/Form/New_version_CRF_WHO_-_Mariana_Medication_export_077b673c092e70a0.csv') as who_form:
        formreader = csv.reader(who_form, delimiter=';')
        header = next(formreader)
        for row in formreader:
            if len(row) != 0:
                report_parent = False
                report_name = False
                #Make instance for form, URI based on Site and participant
                if header[1] == 'Institute Abbreviation':
                    site_id = row[1]
                participant_id = row[0]
                form = URIRef('http://data.who.covid-19-rapid-crf/' + site_id + '-' + participant_id)
                if (form, RDF.type, URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/who-covid-19-rapid-crf')) not in g:
                    g.add((form, RDF.type, URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/who-covid-19-rapid-crf')))
                    print('new form ' + form.toPython())
                group_class_old = 0
                module_class_old = 0
                questionnaire_subsection_old = 0
                column = 0
                for item in header:
                    answer = row[column]
                    if item == 'Record Creation Date' or item == 'Report Creation Date':
                        version_info = Literal(answer)
                    elif item == 'Report Name Custom':
                        report_name = answer
                    elif item == 'Report Parent':
                        if answer != 'FOLLOW UP' and answer!= 'No parent':
                            report_parent = answer
                    elif item in var2class and (answer != ""):
                        #Make instance for question
                        question_class = var2class[item]
                        question = BNode()
                        g.add((question, RDF.type, question_class))
                        #print('            question ' + question_class.toPython())
                        #Get question group, make new if needed, make sure the question is not part of another question
                        group_class = getPartOfClass(question_class)
                        if group_class != group_class_old and n.Question_group in onto.transitive_objects(group_class, RDFS.subClassOf):
                            question_group = BNode()
                            g.add((question_group, RDF.type, group_class))
                            group_class_old = group_class
                            #Make new group part of Module
                            module_class = getPartOfClass(group_class)
                            if module_class != module_class_old:
                                if report_parent: #this group of question is part of an existing module
                                    possible_parents = g.subjects(part_of, form)
                                    #Find parent module
                                    if report_parent == 'HOSPITAL /CENTRE ADMISSION': #Looking for first module of form
                                        module_class = n.Module_1
                                        for pp in possible_parents:
                                            if (pp, RDF.type, n.Module_1) in g:
                                                module = pp
                                                #print('found1 ' + pp.toPython())
                                    elif report_parent[:22] == 'Daily Case Report Form': #Looking for a Daily form
                                        module_class = n.Module_2
                                        for pp in possible_parents:
                                            if (pp, RDF.type, n.Module_2) in g:
                                                if (pp, DC.description, Literal(report_parent)) in g:
                                                    module = pp
                                                    #print('found2 ' + pp.toPython())
                                    elif report_parent == 'DISCHARGE/DEATH': #Looking for discharge module of form
                                        module_class = n.Module_3
                                        for pp in possible_parents:
                                            if (pp, RDF.type, n.Module_3) in g:
                                                module = pp
                                                #print('found3 ' + pp.toPython())
                                else:
                                    #Create new module
                                    module = BNode()
                                    g.add((module, RDF.type, module_class))
                                    print('    new module ' + module_class.toPython() + ' id: ' + module)
                                    g.add((module, part_of, form))
                                    g.add((module, OWL.versionInfo, version_info))
                                    if report_name:
                                        g.add((module, DC.description, Literal(report_name)))
                                    module_class_old = module_class
                            g.add((question_group, part_of, module))
                            print('        new question_group ' + group_class.toPython() + ' part of ' + module)
                        elif URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/C121939') in onto.objects(group_class, RDFS.subClassOf):
                            # Situation where a question is not part of a question_group, but directly part of Module
                            question_group = group_class
                        #Make question part of question-group
                        g.add((question, part_of, question_group))
                        if group_class != group_class_old and URIRef('http://purl.org/vodan/whocovid19crfsemdatamodel/instances/C41116') in onto.transitive_objects(group_class, RDFS.subClassOf): #Not part of a group of questions, but of a question. It is therefor a sub-question
                            #Find URI of parent question
                            parent_question_class = getPartOfClass(question_class)
                            parent_question_uri = g.subjects(RDF.type, parent_question_class).next()
                            g.add((question, part_of, parent_question_uri))

                        if n.Boolean_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # A Boolean question
                            g.add((question, n.has_literal_value, YN2B(answer)))
                        elif n.Date_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # A Date question
                            g.add((question, n.has_literal_value, Literal(datetime.strptime(answer, '%d-%m-%Y').strftime('%Y-%m-%d'), datatype=XSD.date)))
                        elif n.Number_question in onto.transitive_objects(question_class, RDFS.subClassOf):  # A Number question
                            try:
                                int(answer)
                                g.add((question, n.has_literal_value, Literal(answer, datatype=XSD.integer)))
                            except ValueError:
                                g.add((question, n.has_literal_value, Literal(answer, datatype=XSD.decimal)))
                            unit = getUnit(question_class)
                            if unit != None:
                                g.add((question, unit_label, unit))
                            else:
                                print('no unit for: ' + question_class.toPython())
                        elif n.PNNot_done_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # A Pos/Neg/Not done question
                            g.add((question, n.has_value, PNN2subject(answer)))
                        elif n.YNU_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # A Yes/No/Unknown
                            g.add((question, n.has_value, YNU2subject(answer)))
                        elif n.Text_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # Free text question
                            g.add((question, n.has_literal_value, Literal(answer)))
                        elif n.List_Question in onto.transitive_objects(question_class, RDFS.subClassOf):  # List of values question
                            #print(question_class, answer)
                            answer_list_uri = hasLOV(question_class)
                            answer_list = onto.subjects(RDF.type, answer_list_uri)
                            for list_item in answer_list:
                                for labels in onto.preferredLabel(list_item):
                                    if answer in labels[1]:
                                        g.add((question, n.has_value, list_item))
                                        #print(list_item)
                        #print(answer)
                    column += 1

g.serialize(file_base_name + '_rdf.ttl', format='ttl')
