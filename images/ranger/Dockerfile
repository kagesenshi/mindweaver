# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/ranger:2.8.0

COPY ranger.sh /home/ranger/scripts/ranger.sh
COPY create-ranger-services.py /home/ranger/scripts/create-ranger-services.py
USER root
RUN chmod +x /home/ranger/scripts/ranger.sh /home/ranger/scripts/create-ranger-services.py
USER ranger
