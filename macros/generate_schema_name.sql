{#
  Sem esta macro o dbt juntaria o schema do perfil com o do modelo (dbo_silver).
  Aqui cada ambiente tem o seu Warehouse e há uma só pessoa desenvolvendo, então
  os nomes ficam exatamente "silver" e "gold". Com mais desenvolvedores no mesmo
  Warehouse, rever: um sobrescreveria os modelos do outro.
  https://docs.getdbt.com/docs/build/custom-schemas
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
