import hydrus_api
from pathlib import Path
import json
from loguru import logger
from itertools import product
from collections import defaultdict

ANCHOR_TO_IMPORT_ALIAS = {"kemonoparty": "kemono.party"}


@logger.catch
def run(
	config: dict,
	anchor_name: str,
	file_service_name: str = "all local files",
	tag_service_name: str = "all known tags",
	*,
	deleted: bool = True,
):
	conf_hydrus = config["hydrus"]
	key = conf_hydrus["key"]
	host = conf_hydrus["host"]
	client = hydrus_api.Client(key, host)

	file_service_key = {
		client.get_service(file_service_name)["service"]["service_key"]: {}
	}
	# logger.debug(file_service_key)

	deleted_file_service_key = file_service_key if deleted else {}
	# logger.debug(deleted_file_service_key)

	search = [r"system:has url matching regex https://kemono.su"]
	# search = [
	# 	r"system:hash is 77c8f33f9acb7acddf54b00e4ce8d6e57058b87dcb1751498800a792bfa11819"
	# ]  # test
	file_ids = client.search_files(
		[search],
		file_service_keys=file_service_key,
		deleted_file_service_keys=deleted_file_service_key,
	)["file_ids"]
	# logger.debug(file_ids)

	conf_hydl = config["hydownloader"]

	conf_galdl_user_pth = Path(conf_hydl["database_path"]) / "gallery-dl-config.json"
	with conf_galdl_user_pth.open("rb") as fp:
		conf_galdl_user = json.load(fp)

	# find anchor format
	anchor_object: dict | None = conf_galdl_user["extractor"].get(anchor_name)
	if not anchor_object:
		msg = f"Anchor name {anchor_object} is not yet defined in gallery-dl-user-config.json!"
		raise KeyError(msg)

	archive_format: str = anchor_object["archive-format"]
	# logger.debug(archive_format)

	# attempt to reconstruct anchor
	logger.info(
		"fetching metadata for {} files, this may take a while...",
		len(file_ids),
	)

	tags_service_key = client.get_service("all known tags")["service"]["service_key"]
	anchors: [str] = []
	failed_anchors: [str] = []
	metadatas = client.get_file_metadata(file_ids=file_ids)["metadata"]
	import_prefix = ANCHOR_TO_IMPORT_ALIAS[anchor_name]
	for metadata in metadatas:
		basket: defaultdict = defaultdict(list)
		basket["hash"].append(("hash", metadata["hash"]))

		# TODO: look at deleted tags as fallback
		# TODO: handle cases multiple namespaces of the same name
		# e.g. file was found on another post id (or user wtf)
		tags = metadata["tags"][tags_service_key]["storage_tags"]["0"]
		# logger.debug("tags={}", tags)

		# only look for namespace tags
		tags = [tag for tag in tags if ":" in tag]
		# logger.debug("tags={}", tags)

		for tag in tags:
			namespace, value = tag.split(":", maxsplit=1)
			# logger.debug("{} | {}", namespace, value)

			if namespace == f"{import_prefix} id":
				basket["id"].append(("id", value))
			elif namespace == f"{import_prefix} service":
				basket["service"].append(("service", value))
			elif namespace == f"{import_prefix} user id":
				basket["user"].append(("user", value))

		# logger.debug("basket={}", basket)

		# create cartesian product of data and finalize formatting structure
		cartesian_tags = product(*basket.values())
		# logger.debug("combination_tags={}", cartesian_tags)

		anchors_to_compile: list = []  # list of anchors to create
		for cartesian_tag in cartesian_tags:
			d: dict = {}
			for tag in cartesian_tag:
				# logger.debug("tag={}", tag)
				namespace, value = tag
				d[namespace] = value
			anchors_to_compile.append(d)

		# logger.debug("anchors_to_compile={}", anchors_to_compile)
		try:
			for anchor_to_compile in anchors_to_compile:
				# logger.debug("anchor_to_compile={}", anchor_to_compile)
				anchor = anchor_name + archive_format.format(**anchor_to_compile)
				anchors.append(anchor)
		except KeyError as err:
			md5 = basket["hash"][0][1]
			msg = f'archive placeholder "{err.args[0]}" not found for hash {md5}'
			logger.warning(msg)
			failed_anchors.append(md5)

	# prepare query
	anchors_str = ",\n\t".join(f"('{a}')" for a in anchors)
	anchor_query_pth = Path("./anchor_query.tmp")
	with anchor_query_pth.open("w") as fp:
		fp.write(f"insert or ignore into archive (entry) values{anchors_str};")

	logger.success("wrote final query to ./anchor_query.tmp")

	failed_pth = Path("./anchor_failed.tmp")
	if failed_anchors:
		with failed_pth.open("w") as fp:
			fp.write("\n".join(failed_anchors))
		logger.info("failed hashes were written to ./anchor_failed.tmp")
