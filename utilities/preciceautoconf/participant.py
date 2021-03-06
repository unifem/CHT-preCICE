import logging
import sys
from interface import *


class ParticipantFactory:

    def get_participant(name, data, steady_state=False):
        if data["solver"] == "OpenFOAM":
            return OpenFOAMParticipant(name, data, steady_state)
        elif data["solver"] == "Code_Aster":
            return CodeAsterParticipant(name, data, steady_state)
        elif data["solver"] == "CalculiX":
            return CalculiXParticipant(name, data, steady_state)
        else:
            logging.error("Participant of type", data["solver"], "is not implemented.")
            sys.exit(1)

    get_participant = staticmethod(get_participant)


class Participant(object):

    def __init__(self, name, data, steady_state):
        self.name = name
        self.solver_type = None
        self.steady_state = steady_state
        self.interfaces = []
        self.directory = None
        self.domain_decomposed = None
        self.num_processes = 1
        self.populate_data(data)
        self.data_name_T = "Sink-Temperature-" + self.name
        self.data_name_HTC = "Heat-Transfer-Coefficient-" + self.name

    def add_data_tags_to(self, parent):
        etree.SubElement(parent, etree.QName("data", "scalar"), name=self.data_name_HTC)
        etree.SubElement(parent, etree.QName("data", "scalar"), name=self.data_name_T)

    def add_mesh_tags_to(self, parent):
        for interface in self.interfaces:
            interface.add_mesh_tags_to(parent)

    def add_participant_tag_to(self, parent):
        participant = etree.SubElement(parent, "participant", name=self.name)
        if self.domain_decomposed:
            etree.SubElement(participant, etree.QName("master", "mpi-single"))
        for interface in self.interfaces:
            interface.add_provide_mesh_tags_to(participant)
            interface.partner_interface.add_from_mesh_tags_to(participant)
            interface.add_read_write_mapping_tags_to(participant)

    def get_interfaces_with(self, partner):
        interfaces = []
        for interface in self.interfaces:
            if interface.partner_interface.participant == partner:
                interfaces.append(interface)
        return interfaces

    def has_interfaces_with(self, partner):
        return len(self.get_interfaces_with(partner)) > 0

    def populate_data(self, data):

        # Check and populate basic data that all participants should have
        try:
            self.solver_type = data["solver"]
            self.domain_decomposed = data["domain-decomposed"]
            self.directory = data["directory"]
            data["interfaces"]
        except Exception as e:
            logging.error(str(e) + " attribute not provided for participant " + self.name)
            sys.exit(1)

        if self.domain_decomposed:
            # Check whether domain decomposition is supported by this participant
            if not self.is_domain_decomposition_supported():
                logging.error("Domain decomposition is not supported for solver type " + self.solver_type)
                sys.exit(1)
            # Check whether the number of processes is specified
            try:
                self.num_processes = data["nprocs"]
            except Exception as e:
                logging.error(str(e) + " attribute must be provided for participant " + self.name + " if domain-decomposed is True")
                sys.exit(1)


class OpenFOAMParticipant(Participant):

    def __init__(self, name, data, steady_state):
        super(OpenFOAMParticipant, self).__init__(name, data, steady_state)

    def add_interface(self, name=None):
        interface = OpenFOAMInterface(self, name)
        self.interfaces.append(interface)
        return interface

    def get_run_command(self):
        if self.steady_state:
            solver = "buoyantSimpleFoam_preCICE"
        else:
            solver = "buoyantPimpleFoam_preCICE"
        cmd_str = solver + " -case " + self.directory + " -precice-participant " + self.name
        log_str = " > " + self.name + ".log &"
        if self.domain_decomposed:
            par_prepend = "mpirun -np " + str(self.num_processes) + " "
            par_append = " -parallel"
        else:
            par_prepend = ""
            par_append = ""
        return par_prepend + cmd_str + par_append + log_str

    def is_domain_decomposition_supported():
        return True

    is_domain_decomposition_supported = staticmethod(is_domain_decomposition_supported)


class CalculiXParticipant(Participant):

    def __init__(self, name, data, steady_state):
        super(CalculiXParticipant, self).__init__(name, data, steady_state)

    def add_interface(self, name=None):
        interface = CalculiXInterface(self, name)
        self.interfaces.append(interface)
        return interface

    def get_run_command(self):
        # Todo: check default name of .inp file!
        return "ccx_preCICE -i " + self.directory + "/solid -precice-participant " + self.name + " > " + self.name + ".log &"

    def is_domain_decomposition_supported():
        return False

    is_domain_decomposition_supported = staticmethod(is_domain_decomposition_supported)


class CodeAsterParticipant(Participant):

    def __init__(self, name, data, steady_state):
        super(CodeAsterParticipant, self).__init__(name, data, steady_state)

    def add_interface(self, name=None):
        interface = CodeAsterInterface(self, name)
        self.interfaces.append(interface)
        return interface

    def populate_data(self, data):

        super(CodeAsterParticipant, self).populate_data(data)

        try:
            data["non-linear"]
        except Exception as e:
            logging.error(str(e) + " attribute not provided for Code_Aster participant " + self.name)
            sys.exit(1)

        for interface in data["interfaces"]:
            try:
                    interface["material-id"]
            except Exception as e:
                logging.error(str(e) + " attribute not provided for an interface of Code_Aster participant " + self.name)
                sys.exit(1)

    def get_run_command(self):
        # Todo: check default name of .export file!
        return "export PRECICE_PARTICIPANT=" + self.name + "; as_run --run " + self.directory + "/solid.export > " + self.name + ".log &"

    def is_domain_decomposition_supported():
        return False

    is_domain_decomposition_supported = staticmethod(is_domain_decomposition_supported)