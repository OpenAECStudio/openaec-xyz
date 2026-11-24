# Y-Next bovenop het officiële ERPNext-image (Frappe 16.52.0, ERPNext 16.51.1, Python 3.14).
# Y-Next brengt zijn gebouwde frontend mee: geen Node-build, alleen de app erbij zetten.
FROM docker.io/frappe/erpnext:v16.51.1

ARG INSTALLER_VERSIE=dev
ENV Y_NEXT_INSTALLER_VERSIE=${INSTALLER_VERSIE}

COPY --from=y_next --chown=frappe:root . /home/frappe/frappe-bench/apps/y_next
COPY --chown=frappe:root bench/ /opt/y-next/

# De regeleinden rechtzetten voor wie de map op Windows heeft uitgepakt of gekloond.
RUN sed -i 's/\r$//' /opt/y-next/inrichten.sh /opt/y-next/inrichten.py \
    && chmod +x /opt/y-next/inrichten.sh \
    && uv pip install --quiet --python /home/frappe/frappe-bench/env/bin/python --no-deps \
        -e /home/frappe/frappe-bench/apps/y_next \
    && ln -s /home/frappe/frappe-bench/apps/y_next/y_next/public /home/frappe/frappe-bench/assets/y_next
