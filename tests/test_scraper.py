from xml.etree.ElementTree import Element

import pytest
from requests.exceptions import ConnectionError

from sabogaapi.api_v1.scraper import _utilities


@pytest.mark.parametrize(
    "response_text, expected",
    [
        # Case 1: Successful XML response
        (
            "<items><item id='12345'><name value='Terraforming Mars'/></item></items>",
            True,
        ),
        # Case 2: Invalid XML response -> should return None
        ("<items><item id='12345'><name value='Terraforming Mars'></items>", False),
    ],
)
def test_scrape_api_success(response_text, expected, mocker):
    mock_get = mocker.patch("requests.get")

    mock_response = mocker.MagicMock()
    mock_response.text = response_text
    mock_get.return_value = mock_response

    result = _utilities.scrape_api([12345])

    if expected:
        assert isinstance(result, Element)
        assert result.find("./item").attrib["id"] == "12345"
    else:
        assert result is None


def test_scrape_api_network_error(mocker):
    mock_get = mocker.patch(
        "requests.get", side_effect=ConnectionError("Network error")
    )
    mock_sleep = mocker.patch(
        "sabogaapi.api_v1.scraper._utilities._timeout", return_value=None
    )

    result = _utilities.scrape_api([12345])

    assert result is None
    assert mock_sleep.call_count == 10
    assert mock_get.call_count == 10
