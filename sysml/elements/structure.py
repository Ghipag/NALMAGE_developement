"""
Structural elements are commonly used to describe system hierarchies,
classifications, internal composition, or interfaces.
"""
print('hello form structure')
from sysml.elements.base import *
print('imported base')
from sysml.elements.requirements import *
print('imported requirements')
from sysml.elements.parametrics import *
print('imported parametrics')
from collections import OrderedDict as _OrderedDict
from typing import Dict, List, Optional, Union


class Block(ModelElement):
    """This class defines a block

    Parameters
    ----------
    name : string, default None

    parts : dict or list, default None

    references : dict or list, default None

    values : dict or list, default None

    constraints : dict or list, default None

    flowProperties : dict or list, default None

    multiplicity : int, default 1

    states : dict or list, default None

    """

    def __init__(
        self,
        name: Optional[str] = "",
        parts: Optional[Union[Dict[str, "Block"], List["Block"]]] = None,
        references: Optional[Union[Dict[str, "ModelElement"], List["ModelElement"]]
        ] = None,
        values: Optional[Union[Dict[str, "ValueType"], List["ValueType"]]] = None,
        constraints: Optional[
            Union[Dict[str, "ConstraintBlock"], List["ConstraintBlock"]]
        ] = None,
        flowProperties: Optional[dict] = None,
        multiplicity: int = 1,
        modes: Optional[Union[Dict[str, "Mode"], List["Mode"]]] = None,
    ) -> None:
        super().__init__(name)

        if parts is None:
            self._parts: "_OrderedDict" = _OrderedDict()
        elif isinstance(parts, dict):
            self._parts: "_OrderedDict" = _OrderedDict()
            for key, part in parts.items():
                if isinstance(part, Block):
                    self._parts[key] = part
                else:
                    raise TypeError
        elif isinstance(parts, list):
            self._parts: "_OrderedDict" = _OrderedDict()
            for part in parts:
                if isinstance(part, Block):
                    self._parts[part.name] = part
                else:
                    raise TypeError
        else:
            raise TypeError

        if references is None:
            self._references: "_OrderedDict" = _OrderedDict()
        elif isinstance(references, dict):
            self._references: "_OrderedDict" = _OrderedDict()
            for key, reference in references.items():
                if isinstance(reference, ModelElement):
                    self._references[key] = reference
                else:
                    raise TypeError
        elif isinstance(references, list):
            self._references: "_OrderedDict" = _OrderedDict()
            for reference in references:
                if isinstance(reference, ModelElement):
                    self._references[reference.name] = reference
                else:
                    raise TypeError
        else:
            raise TypeError

        if values is None:
            self._values: "_OrderedDict" = _OrderedDict()
        elif isinstance(values, dict):
            self._values: "_OrderedDict" = _OrderedDict()
            for key, value in values.items():
                if isinstance(value, ValueType):
                    self._values[key] = value
                else:
                    raise TypeError
        elif isinstance(values, list):
            self._values: "_OrderedDict" = _OrderedDict()
            for value in values:
                if isinstance(value, ValueType):
                    self._values[value.name] = value
                else:
                    raise TypeError
        else:
            raise TypeError

        if constraints is None:
            self._constraints: "_OrderedDict" = _OrderedDict()
        elif isinstance(constraints, dict):
            self._constraints: "_OrderedDict" = _OrderedDict()
            for key, constraint in constraints.items():
                if isinstance(constraint, ConstraintBlock):
                    self._constraints[key] = constraint
                else:
                    raise TypeError
        elif isinstance(constraints, list):
            self._constraints: "_OrderedDict" = _OrderedDict()
            for constraint in constraints:
                if isinstance(constraint, ConstraintBlock):
                    self._constraints[constraint.name] = constraint
                else:
                    raise TypeError
        else:
            raise TypeError

        if flowProperties is None:
            self._flowProperties: "_OrderedDict" = _OrderedDict()
        elif isinstance(flowProperties, dict):
            self._flowProperties: "_OrderedDict" = _OrderedDict()
            for key, flowPropertie in flowProperties.items():
                if isinstance(flowPropertie, Block):
                    self._flowProperties[key] = flowPropertie
                else:
                    raise TypeError
        else:
            raise TypeError

        if isinstance(multiplicity, (int, float)):
            self._multiplicity = multiplicity
        else:
            raise TypeError

        if modes is None:
            self._modes: "_OrderedDict" = _OrderedDict()
        elif isinstance(modes, dict):
            self._modes: "_OrderedDict" = _OrderedDict()
            for key, mode in modes.items():
                if isinstance(mode, Mode):
                    self._modes[key] = mode
                else:
                    raise TypeError
        elif isinstance(modes, list):
            self._modes: "_OrderedDict" = _OrderedDict()
            for mode in modes:
                if isinstance(mode, Mode):
                    self._modes[mode.name] = mode
                else:
                    raise TypeError
        else:
            raise TypeError

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if type(name) is str:
            self._name = name
        else:
            raise TypeError

    @property
    def parts(self):
        return self._parts

    @property
    def references(self):
        return self._references

    @property
    def values(self):
        return self._values

    @property
    def constraints(self):
        return self._constraints

    @property
    def flows(self):
        return self._flowProperties

    @property
    def multiplicity(self):
        return self._multiplicity

    @property
    def modes(self):
        return self._modes

    @multiplicity.setter
    def multiplicity(self, multiplicity):
        if isinstance(multiplicity, (int, float)):
            self._multiplicity = multiplicity
        else:
            raise TypeError

    def add_part(self, partName, part):
        """Adds block element to parts attribute

        Parameters
        ----------
        partName : string

        block : Block

        """
        if type(partName) is str and isinstance(part, Block):
            self._parts[partName] = part
        else:
            raise TypeError

    def remove_part(self, partName):
        """Removes block element from parts attribute

        Parameters
        ----------
        partName : string

        """
        self._parts.pop(partName)

    def add_mode(self, modeName, mode):
        """Adds mode element to modes attribute

        Parameters
        ----------
        modeName : string

        mode : Mode

        """
        if type(modeName) is str and isinstance(mode, Mode):
            self._modes[modeName] = mode
        else:
            raise TypeError

    def remove_mode(self, modeName):
        """Removes modeelement from modes attribute

        Parameters
        ----------
        modeName : string

        """
        self._states.pop(modeName)

    def __getitem__(self, elementName):
        if type(elementName) is str:
            if elementName in self._parts.keys():
                return self._parts[elementName]
            elif elementName in self._references.keys():
                return self._references[elementName]
            elif elementName in self._values.keys():
                return self._values[elementName]
            elif elementName in self._constraints.keys():
                return self._constraints[elementName]
            elif elementName in self._flowProperties.keys():
                return self._flowProperties[elementName]
            elif elementName in self._modes.keys():
                return self._modes[elementName]
            else:
                raise KeyError
        else:
            raise TypeError

    def __setitem__(self, elementName, element):
        if type(elementName) is str and isinstance(element, Block):
            self._parts[elementName] = element
        elif type(elementName) is not str:
            raise TypeError
        elif not isinstance(element, Block):
            raise TypeError


class DeriveReqt(Dependency):
    """The derive requirement relationship conveys that a requirement at the
    client end is derived from a requirement at the supplier end.

    Parameters
    ----------
    client : Requirement

    supplier : Requirement

    """

    def __init__(self, client, supplier):
        super().__init__(client, supplier)
        if type(client) is not Requirement:
            raise TypeError
        if type(supplier) is not Requirement:
            raise TypeError


class Satisfy(Dependency):
    """This relationship must have a requirement at the supplier end. SysML
    imposes no constraints on the kind of element that can appear at the client
    end. By convention, however, the client element is always a block

    Parameters
    ----------
    client : ModelElement

    supplier : Requirement

    Note
    ----
    A satisfy relationship assersion does not constitute proof. It is simply
    a mechanism to allocate a requirement to a structural element. Proof of
    satisfaction will come from test cases.

    See also
    --------
    Verify

    """

    def __init__(self, client, supplier):
        super().__init__(client, supplier)
        if type(supplier) is not Requirement:
            raise TypeError


class Package(ModelElement):
    """A Package is a container for a set of model elements, of which may
    consist of other packages.

    Parameters
    ----------
    name : string, default None

    elements : dict or list, default None

    """

    def __init__(
        self,
        name: Optional[str] = "",
        elements: Optional[
            Union[Dict[str, "ModelElement"], List["ModelElement"]]
        ] = None,
    ):
        super().__init__(name)

        if elements is None:
            self._elements: "_OrderedDict" = _OrderedDict()
        elif isinstance(elements, dict):
            self._elements: "_OrderedDict" = _OrderedDict()
            for key, element in elements.items():
                if isinstance(element, ModelElement):
                    self._elements[key] = element
                else:
                    raise TypeError
        elif isinstance(elements, list):
            self._elements: "_OrderedDict" = _OrderedDict()
            for element in elements:
                if isinstance(element, ModelElement):
                    self._elements[element.name] = element
                else:
                    raise TypeError
        else:
            raise TypeError

    def __getitem__(self, elementName):
        "Returns model element specified by its name"
        return self._elements[elementName]

    @property
    def name(self):
        return self._name

    @property
    def elements(self):
        return self._elements

    def add(self, element):
        """Adds a model element to package"""
        if isinstance(element, ModelElement):
            i = 0
            while element not in self.elements.values():
                if isinstance(element, Dependency):
                    i += 1
                    elementName = "".join(
                        [
                            element.__class__.__name__[0].lower(),
                            element.__class__.__name__[1:],
                            str(i),
                        ]
                    )
                else:
                    elementName = element.name
                if elementName not in self._elements.keys():
                    self._elements[elementName] = element
        else:
            raise TypeError

    def remove(self, element):
        """Removes a model element from package"""
        self._elements.pop(element.name)

    def RTM(self):
        """Generates a requirements traceability matrix for model elements
        contained and referenced within package"""
        pass

class Mode(ModelElement):
    """This class defines a mode
    
     Parameters
    ----------
    name : string, default None

    functions : dict or list, default None
    """

    def __init__(
        self, 
        name: Optional[str] = "",
        functions: Optional[Union[Dict[str, "Block"], List["Block"]]] = None,
    ) -> None:
        super().__init__(name)
        
        if functions is None:
            self._functions: "_OrderedDict" = _OrderedDict()
        elif isinstance(functions, dict):
            self._functions: "_OrderedDict" = _OrderedDict()
            for key, function in functions.items():
                if isinstance(function, Function):
                    self._functions[key] = function
                else:
                    raise TypeError
        elif isinstance(functions, list):
            self._functions: "_OrderedDict" = _OrderedDict()
            for function in functions:
                if isinstance(function, Function):
                    self._functions[function.name] = function
                else:
                    raise TypeError
        else:
            raise TypeError

    @property
    def name(self):
        return self._name
    
    @property
    def functions(self):
        return self._functions

    def add_function(self, functionName, function):
        """Adds function element to functions attribute

        Parameters
        ----------
        functionName : string

        function : Function

        """
        if type(functionName) is str and isinstance(function, Function):
            self._functions[functionName] = function
        else:
            raise TypeError

    def remove_function(self, functionName):
        """Removes function element from functions attribute

        Parameters
        ----------
        functionName : string

        """
        self._functions.pop(functionName)

class Function(ModelElement):
    """This class defines a function"""

    def __init__(self, name: Optional[str] = ""):
        super().__init__(name)

    @property
    def name(self):
        return self._name