Installation
============

Requirements
------------

* Python 3.11 or higher
* pip or poetry for package management

Using pip
---------

Clone the repository and install dependencies:

.. code-block:: bash

    git clone https://github.com/JuliusBec/Project_Energy_Tariffs.git
    cd Project_Energy_Tariffs
    pip install -r requirements.txt

Using Docker
------------

Build and run using Docker:

.. code-block:: bash

    docker build -t energy-tariffs .
    docker run -p 5000:5000 energy-tariffs

Development Setup
-----------------

For development, you may want to install additional dependencies:

.. code-block:: bash

    pip install -r requirements.txt
    # Install any additional development dependencies
