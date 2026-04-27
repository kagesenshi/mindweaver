# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

FROM apache/ranger:2.8.0

COPY ranger.sh /home/ranger/scripts/ranger.sh
USER root
RUN chmod +x /home/ranger/scripts/ranger.sh
USER ranger
