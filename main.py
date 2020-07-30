#!/usr/bin/env python3
import os
import pathlib
import pprint
from copy import copy
from typing import List

import aioesphomeapi
import asyncio
from aiofile import AIOFile
import yaml


class Lights(object):
    light_struct = {
        (0, 0x01): "marquee_upper_left",
        (0, 0x02): "marquee_upper_right",
        (0, 0x04): "marquee_lower_left",
        (0, 0x08): "marquee_lower_right",
        (0, 0x10): "bass_left",
        (0, 0x20): "bass_right",
        (1, 0x01): "player_1_menu_left",
        (1, 0x02): "player_1_menu_right",
        (1, 0x04): "player_1_menu_up",
        (1, 0x08): "player_1_menu_down",
        (1, 0x10): "player_1_start",
        (1, 0x20): "player_1_select",
        (2, 0x01): "player_1_back",
        (2, 0x02): "player_1_coin",
        (2, 0x04): "player_1_operator",
        (2, 0x08): "player_1_effect_up",
        (2, 0x10): "player_1_effect_down",
        (3, 0x01): "player_1_1",
        (3, 0x02): "player_1_2",
        (3, 0x04): "player_1_3",
        (3, 0x08): "player_1_4",
        (3, 0x10): "player_1_5",
        (3, 0x20): "player_1_6",
        (4, 0x01): "player_1_7",
        (4, 0x02): "player_1_8",
        (4, 0x04): "player_1_9",
        (4, 0x08): "player_1_10",
        (4, 0x10): "player_1_11",
        (4, 0x20): "player_1_12",
        (5, 0x01): "player_1_13",
        (5, 0x02): "player_1_14",
        (5, 0x04): "player_1_15",
        (5, 0x08): "player_1_16",
        (5, 0x10): "player_1_17",
        (5, 0x20): "player_1_18",
        (6, 0x01): "player_1_19",
        (7, 0x01): "player_2_menu_left",
        (7, 0x02): "player_2_menu_right",
        (7, 0x04): "player_2_menu_up",
        (7, 0x08): "player_2_menu_down",
        (7, 0x10): "player_2_start",
        (7, 0x20): "player_2_select",
        (8, 0x01): "player_2_back",
        (8, 0x02): "player_2_coin",
        (8, 0x04): "player_2_operator",
        (8, 0x08): "player_2_effect_up",
        (8, 0x10): "player_2_effect_down",
        (9, 0x01): "player_2_1",
        (9, 0x02): "player_2_2",
        (9, 0x04): "player_2_3",
        (9, 0x08): "player_2_4",
        (9, 0x10): "player_2_5",
        (9, 0x20): "player_2_6",
        (10, 0x01): "player_2_7",
        (10, 0x02): "player_2_8",
        (10, 0x04): "player_2_9",
        (10, 0x08): "player_2_10",
        (10, 0x10): "player_2_11",
        (10, 0x20): "player_2_12",
        (11, 0x01): "player_2_13",
        (11, 0x02): "player_2_14",
        (11, 0x04): "player_2_15",
        (11, 0x08): "player_2_16",
        (11, 0x10): "player_2_17",
        (11, 0x20): "player_2_18",
        (12, 0x01): "player_2_19",
    }
    powers_of_two = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20]

    def __init__(self, cli):
        self.state = bytearray([0] * 13)
        self.cli = cli
        self.light_to_key = dict()

    async def init_lightmap(self):
        list_of_services = await self.cli.list_entities_services()
        for resource_type in list_of_services:
            for entity in resource_type:
                if type(entity) is aioesphomeapi.LightInfo:
                    self.light_to_key[entity.name] = entity.key

    async def update_light(self, light_name, state):
        try:
            if state:
                transition_length = 0.01
            else:
                transition_length = 0.7
            await self.cli.light_command(
                key=self.light_to_key[light_name],
                state=state,
                brightness=0.5,
                rgb=(232 / 255, 67 / 255, 166 / 255),
                transition_length=transition_length,
            )
        except (KeyError, aioesphomeapi.core.APIConnectionError):
            pass

    async def update_state(self, new_state):
        for byte in range(0, 13):
            for index in self.powers_of_two:
                if (new_state[byte] & index) ^ (self.state[byte] & index):
                    try:
                        await self.update_light(
                            self.light_struct[(byte, index)],
                            bool(new_state[byte] & index),
                        )
                    except (KeyError, AttributeError) as e:
                        pass

        self.state = copy(new_state)


async def generate_reconnection_closure(current_loop, cli, hostname):
    async def try_connect(first_try=True, was_disconnected=True):
        """Try connecting to the API client. Will retry if not successful."""
        if was_disconnected:
            print("Lost connection to {}".format(hostname))

        if not first_try:
            print("Waiting 5 seconds before reconnecting")
            await asyncio.sleep(5)

        try:
            await cli.connect(on_stop=try_connect, login=True)
        except aioesphomeapi.core.APIConnectionError as error:
            print("Could not connect to {}: {}".format(hostname, error))
            current_loop.create_task(
                try_connect(first_try=False, was_disconnected=False)
            )
        else:
            print("Connected to {}".format(hostname))

    return try_connect


async def do_stuff(clis: List[aioesphomeapi.APIClient], sextet_file_path: str):
    lights = [Lights(cli) for cli in clis]
    for light in lights:
        await light.init_lightmap()
        await light.update_light("main_light", False)

    async with AIOFile(
        pathlib.Path(sextet_file_path).expanduser(),
        mode="rb",
    ) as light_pipe:
        current_status = bytearray()
        while True:
            single_byte = await light_pipe.read(1)
            if not single_byte:
                break

            if single_byte != b"\n":
                current_status.append(single_byte[0] & 0x3F)
            else:
                for light in lights:
                    await light.update_state(current_status)
                current_status.clear()

    for light in lights:
        await light.update_light("main_light", False)


async def main(conf):
    main_loop = asyncio.get_running_loop()
    clis = list()

    for device in conf["lights"]:
        cli = aioesphomeapi.APIClient(
            main_loop, device["hostname"], 6053, device["password"]
        )

        reconnection_closure = await generate_reconnection_closure(
            main_loop, cli, device["hostname"]
        )
        try:
            await cli.connect(login=True, on_stop=reconnection_closure)
        except aioesphomeapi.APIConnectionError:
            continue

        print("Connected to {}".format(device["hostname"]))
        list_services = await cli.list_entities_services()
        pprint.pprint(list_services)
        clis.append(cli)

    await asyncio.gather(do_stuff(clis, conf["stepmania_sextet_file"]))

    print("All done")


if __name__ == "__main__":
    with pathlib.Path(__file__).parent.joinpath("config.yml").open() as conf_fp:
        conf_data = yaml.safe_load(conf_fp)

    loop = asyncio.get_event_loop()
    try:
        asyncio.run(main(conf_data))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
