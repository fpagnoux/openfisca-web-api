# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Fields controller"""


import collections
import copy

from . import common
from .. import contexts, conv, model, wsgihelpers


def build_prestation_json(column):
    prestation_json = column.to_json()
    if model.input_variables_extractor is not None:
        input_variables = model.get_cached_input_variables(column)
        prestation_json['input_variables'] = list(input_variables)
    return prestation_json


@wsgihelpers.wsgify
def api1_fields(req):
    ctx = contexts.Ctx(req)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)

    assert req.method == 'GET', req.method
    params = req.GET
    inputs = dict(
        context = params.get('context'),
        )
    data, errors = conv.pipe(
        conv.struct(
            dict(
                context = conv.noop,  # For asynchronous calls
                ),
            default = 'drop',
            ),
        )(inputs, state = ctx)
    if errors is not None:
        return wsgihelpers.respond_json(ctx,
            collections.OrderedDict(sorted(dict(
                apiVersion = 1,
                context = inputs.get('context'),
                error = collections.OrderedDict(sorted(dict(
                    code = 400,  # Bad Request
                    errors = [conv.jsonify_value(errors)],
                    message = ctx._(u'Bad parameters in request'),
                    ).iteritems())),
                method = req.script_name,
                params = inputs,
                url = req.url.decode('utf-8'),
                ).iteritems())),
            headers = headers,
            )

    columns = collections.OrderedDict(
        (name, column.to_json())
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if name not in ('idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen')
        if common.is_input_variable(column)
        )
    columns_tree = collections.OrderedDict(
        (
            dict(
                fam = 'familles',
                foy = 'foyers_fiscaux',
                ind = 'individus',
                men = 'menages',
                )[entity],
            copy.deepcopy(tree),
            )
        for entity, tree in model.tax_benefit_system.columns_name_tree_by_entity.iteritems()
        )
    prestations = collections.OrderedDict(
        (name, build_prestation_json(column))
        for name, column in model.tax_benefit_system.column_by_name.iteritems()
        if common.is_output_formula(column)
        )

    return wsgihelpers.respond_json(ctx,
        collections.OrderedDict(sorted(dict(
            apiVersion = 1,
            columns = columns,
            columns_tree = columns_tree,
            context = data['context'],
            method = req.script_name,
            params = inputs,
            prestations = prestations,
            url = req.url.decode('utf-8'),
            ).iteritems())),
        headers = headers,
        )
