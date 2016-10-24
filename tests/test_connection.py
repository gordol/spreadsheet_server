import pyoo
import unittest
import threading
import os
from .context import SpreadsheetConnection

TEST_SS = "example.ods"
SOFFICE_PIPE = "soffice_headless"
SPREADSHEETS_PATH = "./spreadsheets"

class TestConnection(unittest.TestCase):
    
    def setUp(self):
        soffice = pyoo.Desktop(pipe=SOFFICE_PIPE)
        self.spreadsheet = soffice.open_spreadsheet(
            SPREADSHEETS_PATH + "/" + TEST_SS)

        lock = threading.Lock()
        self.ss_con = SpreadsheetConnection(self.spreadsheet, lock)


    def tearDown(self):
        self.spreadsheet.close()
        
        
    def test_lock_spreadsheet(self):
        self.ss_con.lock_spreadsheet()
        self.assertTrue(self.ss_con.lock.locked())
        self.ss_con.unlock_spreadsheet()

        
    def test_unlock_spreadsheet(self):
        self.ss_con.lock_spreadsheet()
        status = self.ss_con.unlock_spreadsheet()
        self.assertTrue(status)
        self.assertFalse(self.ss_con.lock.locked())


    def test_unlock_spreadsheet_runtime_error(self):
        status = self.ss_con.unlock_spreadsheet()
        self.assertFalse(status)
        self.assertFalse(self.ss_con.lock.locked())
        

    def test_get_xy_index_first_cell(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("A1")
        self.assertEqual(alpha_index, 0)
        self.assertEqual(num_index, 0)


    def test_get_xy_index_Z26(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("Z26")
        self.assertEqual(alpha_index, 25)
        self.assertEqual(num_index, 25)


    def test_get_xy_index_aa3492(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("AA3492")
        self.assertEqual(alpha_index, 26)
        self.assertEqual(num_index, 3491)


    def test_get_xy_index_aaa1024(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("AAA1024")
        self.assertEqual(alpha_index, 702)
        self.assertEqual(num_index, 1023)


    def test_get_xy_index_aab739(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("AAB739")
        self.assertEqual(alpha_index, 703)
        self.assertEqual(num_index, 738)


    def test_get_xy_index_aba1(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("ABA1")
        self.assertEqual(alpha_index, 728)
        self.assertEqual(num_index, 0)


    def test_get_xy_index_abc123(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("ABC123")
        self.assertEqual(alpha_index, 730)
        self.assertEqual(num_index, 122)


    def test_get_xy_index_last_cell(self):
        alpha_index, num_index = self.ss_con._SpreadsheetConnection__get_xy_index("AMJ1048576")
        self.assertEqual(alpha_index, 1023)
        self.assertEqual(num_index, 1048575)


    def test_is_single_cell(self):
        status = self.ss_con._SpreadsheetConnection__is_single_cell("AMJ1")
        self.assertTrue(status)


    def test_is_not_single_cell(self):
        status = self.ss_con._SpreadsheetConnection__is_single_cell("A1:Z26")
        self.assertFalse(status)


    def test_check_single_cell(self):
        status = True
        try:
            self.ss_con._SpreadsheetConnection__check_single_cell("Q56")
        except ValueError:
            status = False
            
        self.assertTrue(status)
        

    def test_check_not_single_cell(self):
        status = True
        try:
            self.ss_con._SpreadsheetConnection__check_single_cell("DD56:Z98")
        except ValueError:
            status = False
            
        self.assertFalse(status)
        

    def test_cell_to_index(self):
        d = self.ss_con._SpreadsheetConnection__cell_to_index("ABC945")

        self.assertTrue(d['row_index'] == 944)
        self.assertTrue(d['column_index'] == 730)


    def test_cell_range_to_index(self):
        d = self.ss_con._SpreadsheetConnection__cell_range_to_index("C9:Z26")

        self.assertTrue(d['row_start'] == 8)
        self.assertTrue(d['row_end'] == 25)
        
        self.assertTrue(d['column_start'] == 2)
        self.assertTrue(d['column_end'] == 25)


    def test_check_for_lock(self):
        status = False
        try:
            self.ss_con._SpreadsheetConnection__check_for_lock()
        except RuntimeError:
            status = True

        self.assertTrue(status)


    def test_check_for_lock_with_lock(self):
        self.ss_con.lock_spreadsheet()
        
        status = False
        try:
            self.ss_con._SpreadsheetConnection__check_for_lock()
        except RuntimeError:
            status = True

        self.assertFalse(status)

        self.ss_con.unlock_spreadsheet()


    def test_check_numeric(self):
        value = self.ss_con._SpreadsheetConnection__convert_to_float_if_numeric("1")
        self.assertTrue(type(value) is float)


    def test_check_not_numeric(self):
        value = self.ss_con._SpreadsheetConnection__convert_to_float_if_numeric("123A")

        self.assertTrue(type(value) is str)


    def test_check_list(self):
        status = False
        try:
            self.ss_con._SpreadsheetConnection__check_list([])
        except ValueError:
            status = True

        self.assertFalse(status)


    def test_check_not_list(self):
        status = False
        try:
            self.ss_con._SpreadsheetConnection__check_list(1)
        except ValueError:
            status = True

        self.assertTrue(status)


    def test_check_1D_list(self):
        status = False
        data = ["1","2","3"]
        try:
            data = self.ss_con._SpreadsheetConnection__check_1D_list(data)
        except ValueError:
            status = True

        self.assertFalse(status)
        self.assertEqual(data, [1.0, 2.0, 3.0])

    def test_check_1D_list_when_2D(self):
        status = False
        data = [["1","2","3"], ["1", "2", "3"]]
        try:
            data = self.ss_con._SpreadsheetConnection__check_1D_list(data)
        except ValueError:
            status = True

        self.assertTrue(status)


    def test_set_single_cell(self):
        self.ss_con.lock_spreadsheet()
        self.ss_con.set_cells("Sheet1", "A1", 1)
        self.assertEqual(self.ss_con.get_cells("Sheet1", "A1"), 1)
        self.ss_con.unlock_spreadsheet()


    def test_set_single_cell_list_of_data(self):
        self.ss_con.lock_spreadsheet()
        status = False
        try:
            self.ss_con.set_cells("Sheet1", "A1", [9,1])
        except ValueError:
            status = True

        self.assertTrue(status)
        self.assertNotEqual(self.ss_con.get_cells("Sheet1", "A1"), 9)
        self.ss_con.unlock_spreadsheet()


    def test_set_cell_range_columnn(self):
        self.ss_con.lock_spreadsheet()
        self.ss_con.set_cells("Sheet1", "A1:A5", [1, 2, 3, 4, 5])
        self.assertEqual(self.ss_con.get_cells("Sheet1", "A1:A5"),
                         (1.0, 2.0, 3.0, 4.0, 5.0))
        self.ss_con.unlock_spreadsheet()


    def test_set_cell_range_row(self):
        self.ss_con.lock_spreadsheet()
        self.ss_con.set_cells("Sheet1", "A1:E1", [1, 2, 3, 4, 5])
        self.assertEqual(self.ss_con.get_cells("Sheet1", "A1:E1"),
                         (1.0, 2.0, 3.0, 4.0, 5.0))
        self.ss_con.unlock_spreadsheet()
        
        
    def test_set_cell_range_2D(self):
        self.ss_con.lock_spreadsheet()
        self.ss_con.set_cells("Sheet1", "A1:B2", [[1,2],[3,4]])
        self.assertEqual(self.ss_con.get_cells("Sheet1", "A1:B2"),
                         ((1.0,2.0),(3.0,4.0)))
        self.ss_con.unlock_spreadsheet()



    def test_set_cell_range_2D_incorrect_data(self):
        self.ss_con.lock_spreadsheet()
        status = False
        try:
            self.ss_con.set_cells("Sheet1", "A1:B2", [9, 9, 9, 9])
        except ValueError:
            status = True

        self.assertTrue(status)
        
        self.assertNotEqual(self.ss_con.get_cells("Sheet1", "A1:B2"),
                         ((9.0,9.0),(9.0,9.0)))
        self.ss_con.unlock_spreadsheet()


    def test_get_sheet_names(self):
        sheet_names = self.ss_con.get_sheet_names()
        self.assertEqual(sheet_names, ['Sheet1']

    )

    def test_save_spreadsheet(self):
        path = "./saved_spreadsheets/" + TEST_SS + ".new"

        if os.path.exists(path):
            os.remove(path)
        
        self.ss_con.lock_spreadsheet()
        status = self.ss_con.save_spreadsheet(TEST_SS + ".new")
        self.assertTrue(status)
        self.assertTrue(os.path.exists(path))
        self.ss_con.unlock_spreadsheet()


    def test_save_spreadsheet_no_lock(self):
        path = "./saved_spreadsheets/" + TEST_SS + ".new"

        if os.path.exists(path):
            os.remove(path)

        status = self.ss_con.save_spreadsheet(TEST_SS + ".new")
        self.assertFalse(status)
        self.assertFalse(os.path.exists("./saved_spreadsheets/" + TEST_SS +
                                       ".new"))

        
if __name__ == '__main__':
    unittest.main()
    
