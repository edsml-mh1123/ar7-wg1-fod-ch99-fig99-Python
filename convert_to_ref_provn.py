import argparse
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, DCTERMS

# -------- Namespaces --------
PROV = Namespace("http://www.w3.org/ns/prov#")
IPCC = Namespace("https://www.ipcc.ch/data/#")
VAR = Namespace("http://openprovenance.org/var#")
ATTR = Namespace("https://www.esmvaltool.org/attribute")
PREP = Namespace("https://www.esmvaltool.org/preprocessor")

# -------- CLI Arguments --------
parser = argparse.ArgumentParser(description="Convert IPCC-style PROV to REF-style PROVN.")
parser.add_argument("input", help="Input TRiG file (e.g., input.trig)")
parser.add_argument("output", help="Output PROVN file (e.g., output.provn)")
args = parser.parse_args()

# -------- Load input TRiG --------
g = Graph()
g.parse(args.input, format="trig")

# -------- Helper Functions --------
def get_label(entity):
    label = g.value(entity, DCTERMS.description) or g.value(entity, DCTERMS.title)
    return str(label) if label else entity.split("#")[-1]

def format_agent(varname, email="", orcid="", github="", institute=""):
    return f"""  agent({varname}, [
    attribute:email='{email}',
    attribute:orcid='{orcid}',
    attribute:github='{github}',
    attribute:institute='{institute}'
  ])\n"""

# -------- Extract Entities --------
input_files = set(g.subjects(RDF.type, URIRef("http://purl.dataone.org/provone/2015/01/15/ontology#Data")))
figures = set(g.subjects(RDF.type, URIRef("http://openprovenance.org/var#Figure")))  # Or provone:Visualization
activities = set(g.subjects(RDF.type, URIRef("http://purl.dataone.org/provone/2015/01/15/ontology#Execution")))

# -------- Generate PROVN --------
ref_provn = "document\n"
ref_provn += "  prefix var <http://openprovenance.org/var#>\n"
ref_provn += "  prefix attribute <https://www.esmvaltool.org/attribute>\n"
ref_provn += "  prefix preprocessor <https://www.esmvaltool.org/preprocessor>\n\n"

# Activities
ref_provn += "  activity(var:preprocessingTask, -, -)\n"
ref_provn += "  activity(var:diagnosticTask, -, -)\n"
ref_provn += "  activity(var:software, -, -)\n"

# Agents
ref_provn += format_agent("var:diagnosticAuthor", orcid="https://orcid.org/0000-0002-6378-6229", github="martina-stockhause", institute="DKRZ")
ref_provn += format_agent("var:recipeAuthor", orcid="https://orcid.org/0000-0002-1234-5678", email="someone@example.org")
ref_provn += "  agent(var:project)\n"

# Entities
for i, input_file in enumerate(input_files):
    label = get_label(input_file)
    ref_provn += f"""  entity(var:inputFile{i+1}, [
    attribute:model_id='{label}',
    attribute:Conventions='CF-1.7'
  ])\n"""

    # Add preprocessed file
    ref_provn += f"""  entity(var:preprocessedFile{i+1}, [
    attribute:model_id='{label}',
    preprocessor:regrid='bilinear',
    preprocessor:convert_units='K to C'
  ])\n"""

    # Link input to preprocessed
    ref_provn += f"  wasDerivedFrom(var:preprocessedFile{i+1}, var:inputFile{i+1}, var:preprocessingTask, -, -)\n"

# Result (figure)
for fig in figures:
    caption = get_label(fig)
    ref_provn += f"""  entity(var:resultFile, [
    attribute:caption='{caption}',
    attribute:realm='atmos',
    attribute:references='doi:10.1234/example'
  ])\n"""

    ref_provn += f"  wasDerivedFrom(var:resultFile, var:preprocessedFile1, var:diagnosticTask, -, -)\n"
    ref_provn += f"  wasAttributedTo(var:resultFile, var:diagnosticAuthor)\n"
    ref_provn += f"  wasAttributedTo(var:resultFile, var:recipeAuthor)\n"

# Recipe
ref_provn += """  entity(var:recipe, [
    attribute:description='IPCC AR7 Figure recipe',
    attribute:references='doi:10.5281/zenodo.1234567'
  ])\n"""

ref_provn += "  wasAttributedTo(var:recipe, var:recipeAuthor)\n"
ref_provn += "  wasAttributedTo(var:recipe, var:project)\n"

# Activity links
ref_provn += "  wasStartedBy(var:preprocessingTask, var:recipe, var:software, -)\n"
ref_provn += "  wasStartedBy(var:diagnosticTask, var:recipe, var:software, -)\n"

ref_provn += "endDocument\n"

# -------- Save output --------
with open(args.output, "w") as f:
    f.write(ref_provn)

print(f"REF-style PROVN exported to '{args.output}'")
