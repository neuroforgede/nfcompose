# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


# FIXME: is this up-to-date?
# Conventions:
# 
# 0. All Entities should use uuid4 ids
# 1. All relationships are modelled by their own table
# 2. Relation Tables are named <owning_relation>_<owned_relation>. In the case of relations where there is no
#    clear ownership defined, this convention can be weakened
# 3. Relation Tables are allowed to have an automatically generated id as Django does not allow multi-column primary keys
# 4. Foreign key constraints have to be generated via migrations as Django does not generate the proper CASCADE code.
# 5. Cascading with relationship tables has to be enforced at the database level via triggers
#