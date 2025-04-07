from .file_transfer import FileTransfer
import pysftp
import os
import stat
import shutil


class SFTPFileTransfer(FileTransfer):
    def __init__(self, host: str, port: int, username: str, password: str, root_path: str):
        super().__init__()
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        self.root_path = root_path
        self.sftp_conn = pysftp.Connection(host=host, port=port, username=username, password=password,
                                           cnopts=cnopts)

    def __dcallback(self, dirname=None, path=None):
        pass

    def __download_file(self, file_path: str) -> None:
        """
        Download file from source to local
        :param file_path: Relative file path in source
        :return: None
        """
        source_file_path = os.path.join(self.root_path, file_path)
        local_file_path = os.path.join(self.local_temp_dir, file_path)
        local_dir = os.path.dirname(local_file_path)
        if not os.path.isdir(local_dir):
            print(f"Create {local_dir} dir in local")
            os.makedirs(local_dir)
            os.chmod(local_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        self.sftp_conn.get(remotepath=source_file_path, localpath=local_file_path)
        print(f"Download file {file_path} from source to local complete")

    def __put_file(self, file_path: str) -> None:
        """
        Put file from local to target
        :param file_path: Relative file path in local
        :return: None
        """
        target_file_path = os.path.join(self.root_path, file_path)
        target_dir = os.path.dirname(target_file_path)

        local_file_path = os.path.join(self.local_temp_dir, file_path)
        local_dir = os.path.dirname(local_file_path)

        if not self.sftp_conn.exists(target_dir):
            self.sftp_conn.makedirs(target_dir)

        if not os.path.isdir(local_dir):
            msg = f"Local temp directory {local_dir} isn't existed"
            raise Exception(msg)

        self.sftp_conn.put(localpath=local_file_path, remotepath=target_file_path)
        print(f"Put file {local_file_path} from local to destination complete")

    def list_all_files(self) -> list[str]:
        """
        List all file paths in source from root path
        :return: (list[str]) a file path list in source
        """
        file_list: list[str] = []

        def add_file(file_path: str):
            relative_path = os.path.relpath(file_path, self.root_path)
            file_list.append(relative_path)

        self.sftp_conn.walktree(remotepath=self.root_path, fcallback=add_file, dcallback=self.__dcallback,
                                ucallback=None)
        return file_list

    def download_files(self) -> None:
        """
        Download all process files from source to local
        :return: None
        """
        for file_path in self.process_files:
            self.__download_file(file_path)

    def put_files(self) -> None:
        """
        Put all process files from local to target
        :return: None
        """
        for file_path in self.process_files:
            local_file_path = os.path.join(self.local_temp_dir, file_path)
            if not os.path.exists(local_file_path):
                msg = f"File {file_path} isn't downloaded to local"
                raise FileNotFoundError(msg)
            else:
                self.__put_file(file_path)
        print("Put all files completed")
        shutil.rmtree(self.local_temp_dir)
        print("Delete temp folder completed")

    def detect_new_files(self, file_list: list[str]) -> list[str]:
        """
        Filter new files which need to be processed from file list
        :param file_list: (list[str]) A file path list which get from source
        :return: (list[str]) A new file path list which need to be processed
        """
        process_files = []
        for file in file_list:
            if not self.sftp_conn.exists(file):
                process_files.append(file)
        print(f"New file list: {', '.join(process_files)}")
        return process_files

    def close(self) -> None:
        """
        Close SFTP connection
        :return: None
        """
        self.sftp_conn.close()
