{{ instructions }}

{% if application_fields %}
<dane_wniosku>
{% for field in application_fields %}
- {{ field }}
{% endfor %}
</dane_wniosku>
{% endif %}

<opis_sytuacji>
{{ situation_description }}
</opis_sytuacji>

{% if pinned_articles %}
<podstawa_prawna>
{% for article in pinned_articles %}
- {{ article }}
{% endfor %}
</podstawa_prawna>
{% endif %}
