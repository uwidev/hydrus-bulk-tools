import hydrus_api
from pathlib import Path
import json
from loguru import logger

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

	test = "system:hash is 15a51d2a65b5b554e6a8fdc8be9301eec04a73a40e84ed11e5f4e569fc905030"
	search = [r"system:has url matching regex https://kemono.su"]
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
		data: dict = {}
		data["hash"] = metadata["hash"]

		# TODO: look at deleted tags as fallback
		tags = metadata["tags"][tags_service_key]["storage_tags"]["0"]
		# logger.debug("tags={}", tags)

		# only look for namespace tags
		tags = [tag for tag in tags if ":" in tag]
		# logger.debug("tags={}", tags)

		for tag in tags:
			namespace, value = tag.split(":", maxsplit=1)
			# logger.debug("{} | {}", namespace, value)

			if namespace == f"{import_prefix} id":
				data["id"] = value
			elif namespace == f"{import_prefix} service":
				data["service"] = value
			elif namespace == f"{import_prefix} user id":
				data["user"] = value

		# logger.debug("data=", data)
		try:
			anchor = anchor_name + archive_format.format(**data)
			anchors.append(anchor)
		except KeyError as err:
			md5 = data["hash"]
			msg = f"key {err.args[0]} not found for hash {md5}"
			logger.warning(msg)
			failed_anchors.append(md5)

	# prepare query
	anchors_str = "".join(f"\n\t('{a}')," for a in anchors)
	anchor_query_pth = Path("./anchor_query.tmp")
	with anchor_query_pth.open("w") as fp:
		fp.write(f"insert or ignore into archive (entry) values{anchors_str};")

	logger.success("wrote final query to ./anchor_query.tmp")

	failed_pth = Path("./anchor_failed.tmp")
	if failed_anchors:
		with failed_pth.open("w") as fp:
			fp.write("\n".join(failed_anchors))
		logger.info("failed hashes were written to ./anchor_failed.tmp")
