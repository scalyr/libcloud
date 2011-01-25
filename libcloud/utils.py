# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

def read_in_chunks(file_like_object, chunk_size=None):
    """
    Return generator which reads and yields file data in chunks.

    @type response: C{File}
    @param response: File like objects which implements the read method.

    @type chunk_size: C{int}
    @param chunk_size: Optional chunk size (defaults to CHUNK_SIZE)
    """

    while True:
        data = file_like_object.read(chunk_size)

        if not data:
            break
        yield data
